from common import *

contract_names=[]
mappings=[]
structs=[]

current_contract=Contract()


def encapsulate_function_definition(ret, name, args):
  indent="  "
  s=""
  s+=ret+" " +name+"(address this_sender, address old_receiver, address old_sender"
  for a in args:
    s+=", " + a
  s+=")\n"
  s+=indent+"{\n"
  s+=indent+"  Globals.msg.receiver=this;\n" 
  s+=indent+"  Globals.msg.sender=this_sender;\n"
  call=name+"("
  for i in range(len(args)):
    if i==0:
      call+=args[i].split(" ")[1]
    else:
      call+=", " + args[i].split(" ")[1]
  call+=")"
  if ret!="void":
    s+=indent+"  " + ret + " res=" + call + ";\n" 
  else: s+=indent+"  " + call + ";\n"
  s+=indent+"  Globals.msg.receiver=old_receiver;\n" 
  s+=indent+"  Globals.msg.sender=old_sender;\n" 
  if ret != "void":
    s+= indent+"  return res;\n" 
  s+=indent+"}\n"

  return s

def rewrite_cross_member_function_call(name, args):
  print "#cross: " + name
  if contains(name, "Globals"): return name
  func_name=""
  callee=""
  s=""
  if contains(name, "call.value"):
    func_name="Globals.send"
    callee=name.split(".call.value")[0]
    callee=callee.replace("msg.sender", "Globals.msg.sender")
    s+=func_name+"(this," + callee + ", Globals.msg.sender, Globals.msg.receiver, " + args[0]
    s+=", 10000, \"\")"
  else:
    parts=name.split(".")
    callee=parts[0]
    func_name=parts[1]
    s+=name+"(this, Globals.msg.sender, Globals.msg.receiver"
    for a in args:
      s+=", "+a
    s+=")"

  return s
    

def strip_decl_var(line):
  #res=""
  #line=line.replace("\n", " ")
  #flag=False
  #for x in line:
  #  if x!=" ":
  #    res=res+x
  #  elif res!="" and flag==False:
  #    res=""
  #    flag=True
  #  elif res!="" and flag:
  #    return res.replace("\"", "")
  line=line.replace("\n", "")
  s=line.split(" ")
  res=s[len(s)-1]
  return res.replace("\"", "")

def get_decl_name(line):
  res=""
  line=line.replace("\n", " ")
  flag=False
  for x in line:
    if x!=" ":
      res=res+x
    elif res!="" and flag==False:
      res=""
      flag=True
    elif res!="" and flag:
      return res.replace("\"", "")

def return_indent(line):
  i=""
  for x in line:
    if x==" ": i=i+x
    else: return i

def boundary(line):
  l=["VariableDeclaration", "FunctionDefinition", "Block"]
  for a in l:
    if contains(line, a): return True
  return False

def read_member_access(lineList, indent):
  a=strip_decl_var(lineList[0])
  #if a=="sender":
  #  return "msg.sender"
  #elif a=="value":
  #  return "msg.value"
  ln=1
  identifier=""
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break
    if indent_==indent+"  ":
      if keyword(line, "Identifier"):
        identifier=strip_decl_var(line)
        break
      if keyword(line, "MemberAccess"):
        identifier=read_member_access(lineList[ln:], indent_)
        break
    ln+=1
  return identifier+"."+a

def read_function_call(lineList, indent):
  name=""
  # to get function name
  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break
    
    if indent_==indent+"  ":
      if keyword(line, "Identifier"):
        name=get_last_literal(line)
      elif keyword(line, "MemberAccess to member"):
        name=read_member_access(lineList[ln:], indent_)
      elif keyword(line, "FunctionCall"):
        name=read_function_call(lineList[ln:], indent_)
      else:
        print "Not supported function call: " + line
        sys.exit(0)

    ln=ln+1
    if name!="": break

  args=[]
  # to collect args
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "Identifier"):
        args.append(get_last_literal(line))
      elif keyword(line, "Literal"):
        args.append(get_last_literal(line))
      elif keyword(line, "IndexAccess"):
        args.append(read_index_access(lineList[ln:], indent_))
      elif keyword(line, "BinaryOperation"):
        args.append(read_binary_operation(lineList[ln:], indent_))
      else:
        print "Not supported function argument: " + line
        sys.exit(0)

    ln=ln+1

  cross_member_function_call=False
  if contains(name, "."):
    cross_member_function_call=True

  s=""

  if not cross_member_function_call:
    s=name+"("
    for i in range(0, len(args)):
      if i!=0:
        s=s+","
      s=s+args[i]
    s=s+")"
  else:
    s=rewrite_cross_member_function_call(name, args)

  return s

def read_mapping(lineList, indent):
  ln=1 
  s=[]
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break
    if keyword(line, "ElementaryTypeName"):
      s.append(strip_decl_var(line))
    ln+=1
  return s

def read_variable_declaration(lineList, indent):
  name=strip_decl_var(lineList[0])

  type_name=""

  rhs=""

  extra=""

  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "TypeName"):
        type_name=strip_decl_var(line)
      elif keyword(line, "Mapping"):
        print "xxxxxxxxx " + line
        s=read_mapping(lineList[ln:], indent_)
        type_name=s[1] + "[]" 
        mappings.append([name, s[0], s[1]])
        current_contract.mappings.append([name, s[0], s[1]])
        rhs="new " + s[1] + "[10]"
        extra+="\n"
        # address [] = new 
        extra+="  " + s[0] + " [] " +name+s[0] +"= new " + s[0] + "[10]";
        extra+=";\n"
        extra+="  int Index"+name+"(" + s[0] + " x)\n"
        extra+="  {\n"
        extra+="    for (int i=0; i<10; i++)\n"
        extra+="      if(x=="+name+s[0]+"[i]) return i;\n"
        extra+="    return -1;\n"
        extra+="  }\n"
      else:
        print "Not supported type name: " + line
        sys.exit()

    ln=ln+1
    if type_name!="":
      break

  # now, let's find the rhs of variable declaration
  while ln<len(lineList):
    
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "Literal"): # a literal is assigned
        rhs=get_last_literal(line)
        break
      elif keyword(line, "FunctionCall"):
        rhs=read_function_call(lineList[ln:], indent_)
        func_name=rhs.split("(")[0]
        if in_list(contract_names, func_name):
          rhs="new " + rhs
          current_contract.dependency.append(func_name)
        break
      elif keyword(line, "MemberAccess to member"):
        rhs=read_member_access(lineList[ln:], indent_)
        break
      elif keyword(line, "IndexAccess"):
        rhs=read_index_access(lineList[ln:], indent_)
        break
      else: 
        print "Not supported rhs: " + line
        sys.exit()

    ln=ln+1
    

  if rhs!="":
    return indent + type_name + " " + name + "=" + rhs + ";\n"+extra
  else:
    return indent + type_name + " " + name + ";\n"+extra

def read_variable_declaration_statement(lineList, indent):

  type_name=""
  name=""

  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break
    if keyword(line, "VariableDeclaration"):
      break
    ln+=1

  name=strip_decl_var(lineList[ln])
  ln+=1

  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"    ":
      if keyword(line, "TypeName"):
        type_name=strip_decl_var(line)
      elif keyword(line, "Mapping"):
        rhs=""
      else:
        print "Not supported type name: " + line
        sys.exit()

    ln=ln+1
    if type_name!="":
      break

  # now, let's find the rhs of variable declaration
  rhs=""
  while ln<len(lineList):
    
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "Literal"): # a literal is assigned
        rhs=get_last_literal(line)
        break
      elif keyword(line, "FunctionCall"):
        rhs=read_function_call(lineList[ln:], indent_)
        func_name=rhs.split("(")[0]
        if inList(contract_names, func_name):
          rhs="new " + rhs
        break
      elif keyword(line, "MemberAccess to member"):
        rhs=read_member_access(lineList[ln:], indent_)
        break
      elif keyword(line, "IndexAccess"):
        rhs=read_index_access(lineList[ln:], indent_)
        break
      else: 
        print "Not supported rhs: " + line
        sys.exit()

    ln=ln+1
    

  if rhs!="":
    return indent + type_name + " " + name + "=" + rhs + ";\n"
  else:
    return indent + type_name + " " + name + ";\n"


def read_param_list(lineList, indent):
  ln=1
  params=[]
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "VariableDeclaration"):
        p=read_variable_declaration(lineList[ln:], indent_)
        p=p.replace(indent_, "")
        p=p.replace(";\n", "")
        p=p.replace(indent_, "")
        params.append(p)
        ln=ln+1
        break
    ln=ln+1

  return params

def read_binary_operation(lineList, indent):
  op=strip_decl_var(lineList[0])
  operands=[]
  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break
    if indent_==indent+"  ":
      if keyword(line, "Identifier"):
        operands.append(strip_decl_var(line))
      elif keyword(line, "Literal"):
        operands.append(strip_decl_var(line))
      elif keyword(line, "BinaryOperation"):
        operands.append(read_binary_operation(lineList[ln:], indent_))
      elif keyword(line, "MemberAccess"):
        operands.append(read_member_access(lineList[ln:], indent_))
      elif keyword(line, "IndexAccess"):
        operands.append(read_index_access(lineList[ln:], indent_))
      else:
        print "Unsupported binary operand: " + line
    ln=ln+1
  return operands[0]+op+operands[1]

def read_index_access(lineList, indent):
  arr_name=""
  index=""
  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "Identifier"):
        if arr_name=="":
          arr_name=strip_decl_var(line)
      elif keyword(line, "MemberAccess to member"):
        if arr_name!="":
          index=read_member_access(lineList[ln:], indent_)
          break
    ln+=1
      
  if in_map(mappings, arr_name):
    return arr_name+"[Index"+arr_name+"("+index+")]"
  else:
    return arr_name+"["+index+"]"

def read_assignment(lineList, indent):
  ass=strip_decl_var(lineList[0])

  lhs=""
  
  ln=1
  # to collect the lhs
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "Identifier"):
        lhs=strip_decl_var(line)
        #ln+=1
        break
      elif keyword(line, "IndexAccess"):
        lhs=read_index_access(lineList[ln:], indent_)
        #ln+=1
        break
      elif keyword(line, "MemberAccess to member"):
        lhs=read_member_access(lineList[ln:], indent_)
        #ln+=1
        break

    ln+=1

  rhs=""
  # to collect the right hand side
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "BinaryOperation"):
        rhs=read_binary_operation(lineList[ln:], indent_)
        #op=strip_decl_var(line)
        #operands=read_operands(lineList[ln:], indent_)
        #rhs=operands[0]+op+operands[1]
        ln+=1
        break
      elif keyword(line, "MemberAccess to member"):
        rhs=read_member_access(lineList[ln:], indent_)
      elif keyword(line, "Literal"):
        rhs=strip_decl_var(line)
        break
    ln+=1
  
  return lhs+ass+rhs+""

def read_expression_statement(lineList, indent):

  expr=""

  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "Assignment using operator"):
        expr+=read_assignment(lineList[ln:], indent_)
      elif keyword(line, "FunctionCall"):
        expr+=read_function_call(lineList[ln:], indent_)
    ln+=1

  return indent+expr+";\n"

def read_tuple_expression(lineList, indent):
  print "read tuple expression"
  s=""
  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "FunctionCall"):
        print lineList[ln+5]
        s+=read_function_call(lineList[ln:], indent_)
    ln+=1

  return s

def read_unary_operation(lineList, indent):
  print "Unary"
  s=""
  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "TupleExpression"):
        s+=read_tuple_expression(lineList[ln:], indent_)
    ln+=1

  return s

def read_if_statement(lineList, indent):

  cond=""
  expr=""

  ln=1
  # to read the cond
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "UnaryOperation"):
        cond="!"+read_unary_operation(lineList[ln:], indent_)
        break
    ln+=1
  
  # to read the if body 
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "ExpressionStatement"):
        expr=read_expression_statement(lineList[ln:], indent_)
        #break
    ln+=1
  
  res=""
  res+=indent+"if("+cond+")\n"
  res+=indent+"{\n"
  res+=expr
  res+=indent+"}\n"
  return res


def read_block(lineList, indent):
  block=""
  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break
    
    if indent_==indent+"  ":
      if keyword(line, "VariableDeclaration"):
        block+=read_variable_declaration_statement(lineList[ln:], indent_)
      elif keyword(line, "ExpressionStatement"):
        block+=read_expression_statement(lineList[ln:], indent_)
      elif keyword(line, "IfStatement"):
        block+=read_if_statement(lineList[ln:], indent_)
    ln+=1


  block+=indent 

  return block

def read_function_definition(lineList, indent):
  #name=strip_decl_var(lineList[0])
  name=get_decl_name(lineList[0])
  args=[]
  ret=""
  body=""
  # to collect function arguments
  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "ParameterList"):
        args=read_param_list(lineList[ln:], indent_) 
        ln=ln+1
        break
    ln=ln+1

  # to collect the return type
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "ParameterList"):
        params=read_param_list(lineList[ln:], indent_) 
        if len(params)==0:
          ret="void"
        else:
          ret=params[0]
        ln=ln+1
        break
    ln=ln+1

  # to collect the function body
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "Block"):
        body=read_block(lineList[ln:], indent_) 
        body="\n" + indent + "{\n" + body + "\n" + indent + "}\n"
        ln=ln+1
        break
    ln=ln+1

  if name=="":
    name="fallback"

  s=indent + ret + " " + name + "("
  num=len(args)
  for i in range(num):
    if i!=0:
      s+=", "
    s+=args[i]

  if body!="":
    s=s+")" + body
  else:
    s+=");\n"

  s2=""
  if name!="fallback":
    s2=encapsulate_function_definition(ret, name, args)
    s2=indent + s2
    #s2=s2.replace("\n", "\n  ")
  

  return s + "\n" + s2
    

def read_contract_definition(lineList, indent):
  name=strip_decl_var(lineList[0])
  s=indent+"class " + name + " extends address\n"
  s=s+"{\n"

  ln=1
  while ln<len(lineList):
    line=lineList[ln]
    indent_=return_indent(line)
    if len(indent_)<=len(indent):
      break

    if indent_==indent+"  ":
      if keyword(line, "VariableDeclaration"):
        s_=read_variable_declaration(lineList[ln:], indent_)
        s=s+s_
      elif keyword(line, "FunctionDefinition"):
        s_=read_function_definition(lineList[ln:], indent_)
        s=s+s_

    ln=ln+1

  s=s+"}\n"
  return s

def parse_contract_names(lineList):
  ln=0
  while ln<len(lineList):
    line=lineList[ln]
    if keyword(line, "ContractDefinition"):
      contract_names.append(strip_decl_var(line))
    ln+=1

## AST to intermediate representation
def ast2in(fname):
  fileHandle=open(fname,"r")
  lineList=fileHandle.readlines()
  fileHandle.close()
  contract_bodys=[]

  parse_contract_names(lineList)

  contracts=[]
  ln=0
  indent=0
  while ln<len(lineList):
    line=lineList[ln]
    if keyword(line, "ContractDefinition"):

      current_contract.clear()
      current_contract.name=strip_decl_var(line)

      indent=return_indent(line)
      s=read_contract_definition(lineList[ln:], indent)
      contract_bodys.append(s)

      current_contract.body=s


      contracts.append(current_contract.copy())
    ln=ln+1
    continue
       

  contracts=sort_contract_list(contracts)

  for contract in contracts:
    print "x " + contract.name
    print contract.mappings
  return contracts

  ##return contract_bodys
  s=""
  #for body in contract_bodys:
  #  s=s+body
  #print mappings
  return s

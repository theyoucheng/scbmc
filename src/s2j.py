#!/usr/bin/env python

import argparse
import re
import sys
import string
from common import *

def is_function_call(s):
  s=s.replace('{', '')
  b1=re.findall(r'(?<=(?<=int\s)|(?<=void\s)|(?<=string\s)|(?<=double\s)|(?<=float\s)|(?<=char\s)).*?(?=\s?\()', s)
  b2=re.findall(r"^\s*[\w_][\w\d_]*\s*.*\s*[\w_][\w\d_]*\s*\(.*\)\s*$", s)
  return b1 and b2


def get_assert_cond(s):
  cond=s
  pos=cond.find('//')
  if pos>0:
    cond=cond[:pos]
  cond=cond.replace(' ', '')
  cond=cond.replace('assert(', '')
  cond=cond.replace(');', '')
  cond=cond.replace('\n', '')
  return cond

def count_assert(fname):
    count=0
    with open(fname) as f:
      for line in f:
        if contains(line, 'assert('): count=count+1
    return count

def rewrite_func_decl(line):
  return line

def rewrite_array_decl(line):
  if contains(line, "mapping"):
    return line
  name=""
  for x in line:
    if x=="[": break
    if x==" " or x=="(":
      name=""
    else: name=name+x


  #tmp=line.split();
  #t=tmp[0].split("(")
  #tt=t[len(t)-1]
  line=line.replace("[]", "")
  s="ArrayList<" + name + "> "
  return line.replace(name, s);

def replace_primitive(line):
  line=line.replace("bool", "boolean")
  line=line.replace("uint8", "int")
  line=line.replace("uint256", "int")
  line=line.replace("uint", "int")
  line=line.replace("int8", "int")
  line=line.replace("int256", "int")
  i=32
  while i>=0:
    s="bytes"+str(i) 
    line=line.replace(s, "int")
    i=i-1
  line=line.replace("byte", "int")
  line=line.replace("float", "double")
  line=line.replace("constant", " ")
  line=line.replace("payable", " ")
  line=line.replace("push", "add")
  line=line.replace("external", " ")
  line=line.replace("internal", " ")
  line=line.replace("public", " ")
  line=line.replace("private", " ")
  line=line.replace("storage", "")
  line=line.replace("constants", "")

  if contains(line, "pragma "):
    line="//" + line
  if contains(line, "contract "):
    line=line.replace("contract ", "class ")
    if contains(line, " is "):
      line=line.replace(" is ", " extends ")
    else:
      line=line.replace("\n", "extends address \n ")
  if contains(line, "require"):
    line=line.replace("require", "__CPROVER_assume")
  if contains(line, "[]"):
    line=rewrite_array_decl(line)
  return line

def simplify_returns(line):
  tmp=line.split("returns")
  t=tmp[len(tmp)-1]
  t=t.replace("(", "")
  t=t.replace(")", "")
  t=t.replace("{", "")
  tmp=t.split()
  t=tmp[0]
  t=t.replace(" ", "")
  t=t.replace("\n", "")
  return t #.replace(" ", "")

def contains_struct(struct_list, x):
  for s in struct_list:
    if contains(x, "("+s+"(") or contains(x, " "+s+"(") or contains(x, "="+s+"("):
      return s
  return ""

def create_mapping(m):
  m=m.replace("mapping", "")
  m=m.replace("(", "")
  m=m.replace(")", "")
  m=m.replace("public", "")
  m=m.replace("=>", " ")
  tmp=m.split();
  var=tmp[len(tmp)-1]
  if contains(tmp[1], "[]"):
    tmp[1]=tmp[1].replace("[]", "")
    tmp[1]="ArrayList<" + tmp[1] + "> "
  s="Map<"+tmp[0] + ", " + tmp[1] + "> " + tmp[2]
  return s
  
def contains_list(line, event_list):
  line=line.split("(")[0]
  line=line.replace(" ", "")
  line=line.replace("\n", "")
  line=line.replace("{", "")
  line=line.replace("(", "")
  line=line.replace(")", "")
  if line=="": return False
  for e in event_list:
    if e==line:
      return True
  return False

def is_comment(line):
  line=line.replace(" ", "")
  return line.find("//")==0 or line.find("/*")==0



def is_address_init(line):
  if not contains(line, "="): return False
  x=line.split("=");
  if len(x)!=2: return False
  tmp=x[0].split(" ")
  if not list_contains(tmp, "address"): return False
  return True

def rewrite_address_init(line):
  if not contains(line, "="): return False
  x=line.split("=");
  if len(x)!=2: return False
  tmp=x[0].split(" ")
  if not list_contains(tmp, "address"): return False
  a=""
  for e in tmp:
    if e != "" and e != "address":
      a=e
      break
  i=0
  z=x[1].split(";")[0]
  z=z.replace(" ", "")
  for l in list(string.ascii_lowercase):
    z=z.replace(l, str(i))
    i=i+1
  return "address " + a + "= new address(" + z + ");\n"
  


def main():
  parser=argparse.ArgumentParser(
    description='Convert Solidity source code to Java')
  parser.add_argument(
    'file', metavar='file', action='store', help='The source file to use')

  args=parser.parse_args()

  fname=args.file 

  res=[] ## ??
  contract_name="" ## ??
  mapping_name=""  ## ??
  mapping_list=[]  ## ??

  struct_list=[] ## a list of structs declared
  # to handle the declaration of a struct
  handling_struct=False
  struct_elements=[]
  structs=""
  structs_global=[]


  event_list=[] # a list of events
  event_open=False
  modifier_list=[] # a list of modifiers


  rewriting_func_decl=False # handling function declaration
  func_decl=""
  func_ini=""
  func_ret=""

  struct_ini=False

  count_par=0
  func_par=0 # to count the number of brackets (for a function decl)
  modifier_open=False
  modifier_count=0
  
  ## to print the global declaration of '__CPROVER_fault'
  #res.append('int __CPROVER_fault0=1;\n')
  cprover_faults=[]

  preprocess_input(fname) # preprocessing input file

  with open(fname) as f:
    lnum=0
    for line in f:

      line=replace_primitive(line)

      if func_par!=0:
        func_par=func_par+line.count("{")
        func_par=func_par+line.count("}")

      count_par=count_par+line.count("{")
      if modifier_open:
         modifier_count=modifier_count+line.count("{")
      count_par=count_par+line.count("}")
      if modifier_open:
         modifier_count=modifier_count+line.count("}")


      if event_open:
        line="//" + line
        if contains(line, ");"): event_open=False

      if contains(line, "event "):
        tmp=line
        line="//" + line
        tmp=tmp.replace("event", "")
        tmp=tmp.split("(")[0]
        tmp=tmp.replace(" ", "")
        event_list.append(tmp)
        if not contains(line, ");"): event_open=True
      elif contains_list(line, event_list):
        line="//" + line

      if modifier_open:
        line="//" + line
        if modifier_count!=0 and modifier_count%2==0:
          modifier_open=False
          modifier_count=0


      if contains(line, "modifier "):
        tmp=line
        line="//" + line
        tmp=tmp.replace("modifier", "")
        tmp=tmp.split("(")[0]
        tmp=tmp.replace(" ", "")
        modifier_list.append(tmp)
        modifier_open=True
        #if contains(line, "{"):
        modifier_count=modifier_count+line.count("{")
        #if contains(line, "}"):
        modifier_count=modifier_count+line.count("}")
        if modifier_count!=0 and modifier_count % 2 ==0:
          modifier_open=False
          modifier_count=0
      elif contains_list(line, modifier_list):
        #for m in modifier_list:
        #print "++++++++++++"
        line="//" + line

      if is_comment(line):
        res.append(line)
        continue

        

      ### struct ini
      st=contains_struct(struct_list, line)
      if st!="":
        line=line.replace(st, "new " + st)
        struct_ini=True
      if struct_ini:
        line=line.replace("{", "")
      if struct_ini and contains(line, ":"):
        x=line.split(":")
        line=x[len(x)-1]
      if struct_ini and contains(line, "}"):
        line=line.replace("}", "")
        struct_ini=False
      if struct_ini and contains(line, ";"):
        struct_ini=False
      ## end

      ### to handle struct declaration
      if contains(line, "struct"):
        tmp=line.replace("struct", "");
        tmp=tmp.replace(" ", "");
        tmp=tmp.replace("{", "");
        tmp=tmp.replace("\n", "");
        struct_list.append(tmp)
        handling_struct=True
        line=line.replace("struct", "class")
        structs=structs+line
        continue

      if handling_struct and contains(line, ";"):
        struct_elements.append(line)
        structs=structs+line
        continue
      elif handling_struct and contains(line, "}"):
        struct_name=struct_list[len(struct_list)-1]
        params=[]
        constructor=struct_name+"("
        for p in struct_elements:
          tmp="___"
          if p!=struct_elements[len(struct_elements)-1]:
            tmp=tmp+","
          p=p.replace(";", tmp)
          constructor=constructor+p
          params.append(p.split()[1].replace(tmp, ""))

        constructor=constructor+") {\n"
        for p in params:
          s=p+"="+p+"___; \n"
          constructor=constructor+s
        constructor=constructor+"}\n"


        handling_struct=False
        struct_elements=[]

        line=constructor+line

        structs=structs+line
        structs_global.append(structs)
        structs=""
        continue
      ### end

      if contains(line, "mapping"):
        mapping_list.append(line)
        line="// " + line
      # contract declaration
      if contains(line, "class"):
        contract_name=line.replace(" ", "")
        contract_name=contract_name.replace("{", "")
        contract_name=contract_name.replace("class", "")
        contract_name=contract_name.replace("\n", "")

      # function declaration
      if contains(line, "function "):
        # tmp=line
        line=line.replace("function", "void")
        name=get_func_name(line)
        if name==contract_name: # constructor
          line=line.replace("void", "")
        rewriting_func_decl=True
      if rewriting_func_decl:
        tmp=line
        if contains(tmp, " returns "):
          tmp0=tmp.split("returns")[0]  
          #func_decl=func_decl+tmp0
          tmp=tmp.split("returns")[1]  
          tmp=tmp.replace("(", "")
          tmp=tmp.replace(")", "")
          x=tmp.replace(" ", "")
          if is_primitive(x, struct_list):
            func_decl=func_decl.replace("void", x)
          else:
            x=tmp.split()[0]
            x=x.replace(" ", "")
            if is_primitive(x, struct_list):
              func_decl=func_decl.replace("void", x)
              func_ini=tmp+";\n"
        else:
          func_decl=func_decl+line
        if contains(line, "{") or contains(line, ";"):
          if contains(line, ";"):
            line=func_decl + ";"
          else:
            line=func_decl
          func_decl=""
          rewriting_func_decl=False
          func_par=func_par+line.count("{")
          func_par=func_par+line.count("}")
        else: line=""

      
      if contains(line, "{") and func_ini!="":
        line=line+"\n"+func_ini
        tmp = func_ini.split()
        func_ret="return " + tmp[1]
        func_ini=""
      if contains(line, "return ") and func_ret!="":
        func_ret=""
      if contains(line, "}") and func_par%2==0:
        func_par=0
        if func_ret!="":
          line=func_ret+"\n"+line
          func_ret=""

      if is_address_init(line):
        line=rewrite_address_init(line)

      res.append(line)

  for s in structs_global:
    print s
  for m in mapping_list:
    print create_mapping(m)
  for l in res:
    print l
  #  sys.stdout.write(l) #print l


if __name__=="__main__":
  main()

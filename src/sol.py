from common import *
import shutil

def is_event_decl(line):
  return contains(line, "event ")

def get_event(line):
  line=line.replace("event", "")
  line=line.split("(")[0]
  line=line.replace(" ", "")
  return line

def is_event_decl_closed(line):
  return contains(line, ");")

def lazy_replacement(line):
  line=line.replace("(msg.sender", "(Globals.msg.sender")
  line=line.replace("=msg.sender", "=Globals.msg.sender")
  line=line.replace("msg.value", "Globals.msg.value")
  line=line.replace("(msg.receiver", "(Globals.msg.receiver")
  line=line.replace("=msg.receiver", "=Globals.msg.receiver")
  line=line.replace("uint8", "int")
  line=line.replace("uint256", "int")
  line=line.replace("uint", "int")
  line=line.replace("int8", "int")
  line=line.replace("int256", "int")
  i=32
  while i>=0:
    s="bytes"+str(i) 
    line=line.replace(s, "String")
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
      line=line.replace("\n", " extends address \n ")
  if contains(line, "require"):
    line=line.replace("require", "__CPROVER_assume")
  #if contains(line, "[]"):
  #  line=rewrite_array_decl(line)
  return line

def is_mapping_decl(line):
  return contains(line, "mapping") and contains(line, "=>")

def using_mapping(line, mappings):
  for m in mappings:
    if contains(line, m[0]+"["): return True
  return False


def get_mapping_tuple(mappings, m):
  m=m.replace("mapping", "")
  m=m.replace("(", "")
  m=m.replace(";", "")
  m=m.replace(")", "")
  m=m.replace("public", "")
  m=m.replace("=>", " ")
  tmp=m.split()
  # var: from, to
  tmp.insert(0, tmp.pop(2))
  for x in mappings:
    #if x[0]==tmp[0] and x[1]==tmp[1] and x[2]==tmp[2]: return x
    if x==tmp: return x

def is_mapping(mappings, x):
  for m in mappings:
    if x==m[0]: return True
  return False

def get_mapping_tuple_by_name(mappings, x):
  for m in mappings:
    if x==m[0]: return m

# for now, let's hope that there exist no two mappings
# at the same time
def rewrite_mapping(line, mappings):
  line=line.replace(" ", "")
  x=""
  for i in line:
    y=x+i
    if not y.isalnum() and not(i=="_"):
      if i=='[':
        if is_mapping(mappings, x):
          t=get_mapping_tuple_by_name(mappings, x)
          index=x+"["+"Index" + t[0] + '('
          line=line.replace(x+'[', index)
          break
      else:
        x=""
        continue
    else:
      x=y
  c=0
  nl=""
  for i in line:
    if i=='(': c=0
    if i=='[' or i==']': c=c+1
    if i==']' and c % 2 != 0:
      nl=nl+")]"
      continue
    nl=nl+i
  return nl
  
def preprocess_input(fname):
  shutil.copy2(fname, fname+"_")
  with open(fname+"_", 'r+') as f:
    lines = f.readlines()
    f.seek(0)
    f.truncate()
    for line in lines:
      line=remove_comments(line)
      line = line.replace("{", "\n {")
      line = line.replace(" returns ", "\n returns ")
      line=lazy_replacement(line)
      f.write(line)

def is_func_decl(line):
  return contains(line, "function ") or contains(line, "function(")

def is_fallback(line):
  line=line.replace(" ", "")
  return contains(line, "function()")

def transform_mapping_decl(t):
   res="public " + t[2] + "[] " + t[0] + " = new " + t[2] + "[10];\n" 
   res = res + t[1] + "[] " + t[0] + t[1] + " = new " + t[1] + "[10];\n"
   res = res + "int Index" + t[0] + "(" + t[1] + " in)\n"
   res = res + "{\n"
   res = res + "  for (int i=0; i<10; ++i)\n"
   res = res + "    if(" + t[0]+t[1] + "[i]==in) return i;\n"
   res = res + "  return -1\n"
   res = res + "}\n"
   return res

def return_type(tmp):
  tmp=tmp.split("returns")[1]  
  tmp=tmp.replace("(", "")
  tmp=tmp.replace(")", "")
  x=tmp.replace(" ", "")
  return x

def return_type_(tmp):
  tmp=tmp.split("returns")[1]  
  tmp=tmp.replace("(", "")
  tmp=tmp.replace(")", "")
  x=tmp.split()[0]
  x=x.replace(" ", "")
  return x
 

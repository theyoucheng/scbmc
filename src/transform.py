from common import *
from sol import *

def rewrite_contracts(fname, address_dict, structs, mappings, contract_set):
  s="" # to return

  event_list=[]
  event_decl_open=False

  rewriting_func_decl=False
  func_decl=""

  with open(fname) as f:
    for line in f:
      if not line.strip(): continue  # skip the empty line


      ## event
      if is_event_decl(line):
        event_list.append(get_event(line))
        if not is_event_decl_closed(line):
          event_decl_open=True
        line="" #"// " + line
      elif event_decl_open:
        line="" #"// " + line
        if is_event_decl_closed(line):
          event_decl_open=False
      ##

      ## mapping
      if is_mapping_decl(line):
        t=get_mapping_tuple(mappings, line)
        line=transform_mapping_decl(t)
      elif using_mapping(line, mappings):
        line=rewrite_mapping(line, mappings)
      ## ...

      ## function
      if is_func_decl(line):
        if is_fallback(line):
          line="public void fallback()\n"
        else:
          line=line.replace("function ", "void ")
          name=get_func_name(line)
          if in_list(contract_set, name):
            line=line.replace("void", "")
          rewriting_func_decl=True
          #func_decl="public " + line
      if rewriting_func_decl:
        tmp=line
        if keyword(tmp, "returns"):
          func_decl=func_decl+tmp.split("returns")[0]
          t=return_type(tmp)
          if is_primitive(t) or in_list(structs, t):
            func_decl=func_decl.replace("void", x)
          else:
            x=return_type_(tmp)
            print "ddd " + x
            if is_primitive(x) or in_list(stucts, x):
              func_decl=func_decl.replace("void", x)
              func_ini=t+";\n"
        else:
          func_decl=func_decl+line
        if keyword(line, "{"):
          line="public " + func_decl
          func_decl=""
          rewriting_func_decl=False
        elif keyword(line, ";"):
          line="public " + func_decl+";"
          func_decl=""
          rewriting_func_decl=False
        else: line=""
      ##

      if not (line==""): s=s+line

  return s

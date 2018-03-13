
from common import *
import json

# to instantiate
def contract_ins(l):
  return l.replace(" ", "")

def parse_addresses(fname):
  json_string=""
  with open(fname, 'r') as myfile:
    json_string=myfile.read()
  
  data=json.loads(json_string)
  address_dict=dict()

  for contract in data["blockchain"]:
    cname=contract_ins(contract)
    address_dict[cname]=data["blockchain"][contract]["address"]

  return address_dict

def parse_contracts(fname):
  json_string=""
  with open(fname, 'r') as myfile:
    json_string=myfile.read()
  
  data=json.loads(json_string)
  contract_set=set()

  for contract in data["blockchain"]:
    contract_set.add(contract.split()[1])

  return contract_set

def parse_structs(fname):
  #print fname
  structs=[]
  with open(fname) as f:
    for line in f:
      if contains(line, "struct"):
        tmp=line.replace("struct", "");
        tmp=tmp.replace(" ", "");
        tmp=tmp.replace("{", "");
        tmp=tmp.replace("\n", "");
        structs.append(tmp)
  return structs

def parse_mappings(fname):
  mappings=[]
  with open(fname) as f:
    for line in f:
      if contains(line, "mapping") and contains(line, "=>"):
        m=line
        m=m.replace("mapping", "")
        m=m.replace("(", "")
        m=m.replace(";", "")
        m=m.replace(")", "")
        m=m.replace("public", "")
        m=m.replace("=>", " ")
        tmp=m.split()
        # var: from, to
        tmp.insert(0, tmp.pop(2))
        mappings.append(tmp)
  return mappings

def parse_config(fname, maps):
  json_string=""
  with open(fname, 'r') as myfile:
    json_string=myfile.read()
  
  data=json.loads(json_string)
  contracts=[]
  Blockchain=""
  statics=""
  start=""
  i=0
  for contract in data["blockchain"]:
    line=contract.split()
    name=line[1]+line[2]
    statics=statics+"public static " + line[1] +  " " + name + " = new " + line[1] + "();\n"
    s=""
    for e in data["blockchain"][contract]:
      if e=="address":
        s=s+name+".id=" + "\"" + data["blockchain"][contract][e] + "\";\n"
        s=s+"Globals.addresses[" + str(i) + "]=" + name + ";\n"
        i=i+1
      elif e=="balance":
        s=s+name+".balance=" + str(data["blockchain"][contract][e]) + ";\n"
      elif map_tuple_contains(maps, e):
        tup=find_tuple_in_map(maps, e)
        j=0
        array_name=tup[0]+tup[1]
        for x in data["blockchain"][contract][e]:
          if not tup[2]=="String":
            s = s + name + "." + e + "[" + str(j) + "]=" + str(data["blockchain"][contract][e][x]) + ";\n"
          else:
            s = s + name + "." + e + "[" + str(j) + "]=\"" + str(data["blockchain"][contract][e][x]) + "\";\n"
          s=s+name+"."+array_name+"[" + str(j) + "]=" + find_contract_by_address(data, x) + ";\n"
          j=j+1
    contracts.append(s)

  for transaction in data["transactions"]:
    start=data["transactions"][transaction]["code"]
  
  # to print out Env
  s=""
  s+="class Env {\n"
  s+=statics
  s+="public static void init() { \n"
  for c in contracts:
    s+=c
  s+="for(int i=0; i<Globals.noa; ++i)\n"
  s+="  Globals.trans_depth[i]=0;\n"
  s+=start+"\n"
  s+="}\n"
  s+="}\n"
  return s

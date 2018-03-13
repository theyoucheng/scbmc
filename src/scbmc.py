#!/usr/bin/env python
import argparse
from parsers import *
from Globals import *
from transform import *
from ast2in import *


def main():
  
  # cmd line inputs
  parser=argparse.ArgumentParser(
    description='SCBMC: Smart Contract Bounded Model Checker')
  parser.add_argument('file', action='store', nargs='+')
  #parser.add_argument('file', type=argparse.FileType('r'), nargs='+')
  parser.add_argument(
    '--config', metavar='config', action='store', help='The blockchain info')
  parser.add_argument(
    '--ast', metavar='ast', action='store', help='The abstract syntax tree')
  parser.add_argument(
    '--solver', metavar='solver', action='store', help='The BMC solver')
  parser.add_argument(
    '--unwind', metavar='unwind', action='store', default="-1", help='Number of unwinding')

  args = parser.parse_args()

  #contract_fnames=[]
  #for f in args.file:
  #  contract_fnames.append(f)
  #contract_set=parse_contracts(args.config)
  #print contract_set
  ##print address_dict
  #structs=[]
  #for f in contract_fnames:
  #  structs = structs + parse_structs(f)
  #print structs
  #mappings=[]
  #for f in contract_fnames:
  #  mappings = mappings + parse_mappings(f)
  #print mappings

  s=write_globals()

  fname=args.file[0] ## input file
  #s+=ast2in(fname)

  mappings=[]

  contracts=ast2in(fname)

  for contract in contracts:
    s+=contract.body
    mappings+=contract.mappings

  s+=parse_config(args.config, mappings)

  unwind=int(float(args.unwind))

  print "##########################"
  #print "#unwind: " + str(unwind)
  #print "#config: " + config_fname
  #print "#contract_fnames: "
  #print contract_fnames
  print "#ast: " + fname
  print mappings
  print "##########################"

  ### to parse blockchain and obtain addresses of contracts  
  #address_dict=parse_addresses(args.config)

  #s=write_globals()
  #for f in contract_fnames:
  #  s=s+rewrite_contracts(f, address_dict, structs, mappings, contract_set)
  s=lazy_replacement(s)
  s+=write_main()
  f = open("Veri.java","w") 
  f.write(s)
  f.close()
  
  jbmc=args.solver
  jbmc=os.path.abspath(jbmc)
  print jbmc
  cmd="javac Veri.java && "+ jbmc + " Veri.class --partial-loops"
  if unwind>0: cmd+=" --unwind " + str(unwind)
  os.system(cmd)
  
  #print s

if __name__=="__main__":
  main()

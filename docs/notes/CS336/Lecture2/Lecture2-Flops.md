---
title : Lecture 2 :FLOPs、计算速度与显存带宽
---
# 1. FLOPs 与 FLOP/s

## FLOPs

**FLOPs** 是 Floating-Point Operations 的缩写，表示完成某项任务需要进行多少次浮点运算，用来衡量一个任务的计算量。

例如：

```text
某次矩阵乘法需要 10 TFLOPs
```

表示这次矩阵乘法一共需要大约：

$$
10 \times 10^{12}
$$

次浮点运算。

## FLOP/s

**FLOP/s** 是 Floating-Point Operations Per Second 的缩写，也常写成 **FLOPS**，表示硬件每秒能够完成多少次浮点运算，用来衡量硬件的计算速度。

例如：

```text
某块 GPU 的计算速度为 100 TFLOP/s
```

表示这块 GPU 理论上每秒可以完成：

$$
100 \times 10^{12}
$$

次浮点运算。

因此：

```text
FLOPs  → 一个任务总共需要计算多少次
FLOP/s → 硬件每秒最多能够计算多少次
```

这两个概念的含义不同。

只考虑计算、不考虑数据搬运和其他开销时，理论计算时间为：

$$
T_{\text{compute}}
=
\frac{\text{任务需要的 FLOPs}}
{\text{硬件的 FLOP/s}}
$$

例如，某次计算需要 10 TFLOPs，而 GPU 的计算速度为 100 TFLOP/s：

$$
T_{\text{compute}}
=
\frac{10\ \text{TFLOPs}}
{100\ \text{TFLOP/s}}
=
0.1\ \text{s}
$$

---

# 2. 计算矩阵乘法的 FLOPs

假设进行矩阵乘法：

$$
X_{B\times D}W_{D\times K}
=
Y_{B\times K}
$$

对应代码为：

```python
x = torch.randn(B, D)
w = torch.randn(D, K)

y = x @ w
```

张量形状为：

```text
x.shape = [B, D]
w.shape = [D, K]
y.shape = [B, K]
```

输出矩阵中的每个元素为：

$$
y_{i,j}
=
\sum_{d=1}^{D}x_{i,d}w_{d,j}
$$

展开后为：

$$
y_{i,j}
=
x_{i,1}w_{1,j}
+
x_{i,2}w_{2,j}
+
\cdots
+
x_{i,D}w_{D,j}
$$

计算一个输出元素，需要：

- $D$ 次乘法；
- $D-1$ 次加法。

因此，一个输出元素的计算量为：

$$
D+(D-1)=2D-1
$$

输出矩阵中一共有：

$$
B\times K
$$

个元素，因此更加精确的总计算量为：

$$
\text{FLOPs}
=
BK(2D-1)
$$

当 $D$ 很大时，可以忽略其中的常数 $-1$：

$$
2D-1\approx2D
$$

所以矩阵乘法的计算量通常近似写成：

$$
\boxed{
\text{FLOPs}
\approx
2BDK
}
$$

对应代码为：

```python
actual_num_flops = 2 * B * D * K
```

这里乘以 `2`，是因为一次乘加过程包含：

```text
一次乘法 + 一次加法 = 2 FLOPs
```

需要注意，不是把 $2D-1$ 近似成 $D$，而是近似成 $2D$。

虽然 GPU 可能使用一条 FMA，也就是 Fused Multiply-Add 指令，同时完成乘法和加法，但它仍然完成了两次浮点运算，所以通常记作：

$$
1\ \text{FMA}
=
2\ \text{FLOPs}
$$

---

# GPU 计算与显存带宽

执行一个 GPU 操作，通常需要经历三个主要步骤：

```text
1. 从显存中读取输入
2. GPU 执行计算
3. 将输出写回显存
```

因此，一个操作需要多长时间，主要和两个指标有关：

1. GPU 的计算速度，也就是 FLOP/s；
2. 显存的数据传输速度，也就是 Memory Bandwidth。

即使GPU计算速度很快，如果数据传输速度太慢，GPU也只能等待数据。

反过来，即使数据传输速度很快，如果 GPU 计算速度不够，也需要等待计算完成。

---

## 1. 两种不同的时间

### 计算时间

计算时间取决于任务总计算量和 GPU 的计算速度：

$$
T_{\text{compute}}
=
\frac{\text{Operation FLOPs}}
{\text{GPU FLOP/s}}
$$

### 数据搬运时间

数据搬运时间取决于需要传输的数据量和显存带宽：

$$
T_{\text{memory}}
=
\frac{\text{Transferred Bytes}}
{\text{Memory Bandwidth}}
$$

在理想情况下，GPU 可以让一部分计算与数据搬运同时进行，因此总运行时间可以近似写成：

$$
T
\approx
\max
\left(
T_{\text{compute}},
T_{\text{memory}}
\right)
$$

这里使用 `max`，是因为最终速度主要取决于更慢的一部分。

---

## 2. H100 的两个硬件指标

课程代码中写道：

```python
h100_flop_per_sec = 1979e12 / 2  # Half without sparsity
h100_bytes_per_sec = 3.35e12
```

这两个数字表示的不是同一种东西。

### H100 的计算速度

```python
h100_flop_per_sec = 1979e12 / 2
```

其中：

```text
1979e12 = 1979 × 10¹² FLOP/s
```

也就是：

$$
1979\ \text{TFLOP/s}
$$

这里的数值包含结构化稀疏带来的理论加速。

注释中写着：

```python
# Half without sparsity
```

表示这里不考虑稀疏性，因此除以 2：

$$
\frac{1979}{2}
=
989.5
$$

所以：

$$
h100\_flop\_per\_sec
=
989.5\times10^{12}
$$

也就是：

$$
989.5\ \text{TFLOP/s}
$$

它表示 H100 在对应低精度计算下的理论峰值计算速度。

### H100 的显存带宽

```python
h100_bytes_per_sec = 3.35e12
```

表示：

$$
3.35\times10^{12}\ \text{bytes/s}
$$

也就是：

$$
3.35\ \text{TB/s}
$$

它表示 H100 的 HBM 每秒最多能够向 GPU 计算单元传输约 3.35 TB 的数据。

注意：

```text
989.5 TFLOP/s → 计算速度
3.35 TB/s     → 数据传输速度
```

它们的单位和含义都不同，不能直接比较数值大小。

---

# CPU、GPU 与 HBM

## CPU

CPU 可以理解为整个程序的控制者，主要负责：

- 执行 Python 程序；
- 运行 PyTorch 的上层代码；
- 准备和调度任务；
- 启动 CUDA Kernel；
- 进行数据加载；
- 管理文件、网络和程序流程。

例如：

```python
y = x @ w
```

这行 Python 代码首先由 CPU 执行。

但是对于大型矩阵乘法，CPU 通常不会亲自完成所有乘法和加法，而是向 GPU 发出一个任务：

```text
请执行这次矩阵乘法
```

CPU 随后会启动对应的 CUDA Kernel。

## GPU

GPU 是加速器，主要负责大量可以并行执行的计算。

GPU 内部包括：

- SM；
- CUDA Core；
- Tensor Core；
- 寄存器；
- Shared Memory；
- L2 Cache；
- 显存控制器。

矩阵乘法中的乘法和加法，主要由 GPU 内部的 Tensor Core 或 CUDA Core 完成。

## HBM

HBM 全称为：

```text
High Bandwidth Memory
```

也就是高带宽显存。

它用于存储：

- 模型参数；
- 输入张量；
- 中间激活值；
- 梯度；
- Optimizer State；
- 输出结果。

需要注意：

> HBM 只负责存储和传输数据，并不负责真正进行矩阵乘法。

H100 使用 HBM。

RTX 3090 使用的是 GDDR6X。虽然存储技术不同，但在这个计算过程中，它们扮演的角色基本相同，都是 GPU 的外部显存。

---

# GPU 执行矩阵乘法的过程

假设执行：

```python
x = torch.ones(B, D, device="cuda")
w = torch.randn(D, K, device="cuda")

y = x @ w
```

由于指定了：

```python
device="cuda"
```

因此 `x` 和 `w` 都存储在 GPU 显存中。

整个计算过程大致为：

```text
CPU 执行 Python 代码
        ↓
CPU 启动矩阵乘法 CUDA Kernel
        ↓
x 和 w 已经存储在 GPU 显存中
        ↓
从 HBM 或 GDDR 中读取一小块 x 和 w
        ↓
数据经过 L2 Cache
        ↓
数据进入 Shared Memory 和寄存器
        ↓
Tensor Core 或 CUDA Core 执行乘法和累加
        ↓
得到一小块输出 y
        ↓
将 y 写回 GPU 显存
```

GPU 通常不会一次性把完整矩阵放入计算单元。

它会将矩阵切分成许多小块，这些小块称为：

```text
Tile
```

然后反复执行：

```text
读取一小块数据
→ 进行计算
→ 尽可能重复使用数据
→ 写回结果
```

这种分块方法可以让一个从显存中读取的元素参与多次计算，从而减少显存读取次数。

---

# 矩阵乘法需要搬运多少数据

对于：

$$
X_{B\times D}W_{D\times K}
=
Y_{B\times K}
$$

需要进行以下数据传输：

1. 读取矩阵 $X$；
2. 读取矩阵 $W$；
3. 写入矩阵 $Y$。

三个矩阵的元素数量分别为：

$$
X:BD
$$

$$
W:DK
$$

$$
Y:BK
$$

如果每个元素占用 $s$ 个字节，那么理想情况下需要搬运的数据量为：

$$
\text{Bytes}
=
s(BD+DK+BK)
$$

不同数据类型中，每个元素占用的字节数不同：

```text
FP32  → 4 bytes
FP16  → 2 bytes
BF16  → 2 bytes
INT8  → 1 byte
```

例如，使用 FP16 时：

$$
s=2
$$

所以：

$$
\text{Bytes}
=
2(BD+DK+BK)
$$

这里计算的是理想情况下的最低数据搬运量。

实际运行时还会受到以下因素影响：

- Cache 是否命中；
- 矩阵如何分块；
- 数据是否被重复读取；
- 中间结果是否需要写回显存；
- 数据布局是否连续。

---


# Arithmetic Intensity 与 Accelerator Intensity

判断一个操作是 `Compute-bound` 还是 `Memory-bound`，需要同时考虑：

1. 这个操作需要进行多少计算、搬运多少数据；
2. GPU 的计算速度和显存带宽分别有多高。

因此，这里有两个不同的 Intensity。

## 1. Arithmetic Intensity

Arithmetic Intensity 称为**算术强度**。
定义为：

$$
I_{\text{op}}
=
\frac{\text{Operation FLOPs}}
{\text{Transferred Bytes}}
$$

单位为：

```text
FLOPs/byte
```

它表示：

> 这个操作每从显存中搬运一个字节的数据，需要进行多少次浮点运算。



需要注意，Arithmetic Intensity 是**操作的属性**，它与操作类型、张量形状、数据类型、缓存复用和 Kernel 实现有关。

---

## 2. Accelerator Intensity

Accelerator Intensity 描述的是 GPU 硬件本身的计算能力和显存带宽之间的比例。

定义为：

$$
I_{\text{accelerator}}
=
\frac{\text{Peak FLOP/s}}
{\text{Memory Bandwidth}}
$$

单位同样为：

```text
FLOPs/byte
```

它表示：

> GPU 每从显存获得一个字节的数据，最多能够配套完成多少次浮点运算。

这个数也常被称为：

```text
Machine Balance
```

在 Roofline Model 中，它对应计算屋顶与带宽屋顶相交的位置，也称为：

```text
Ridge Point
```


Arithmetic Intensity  → 操作的属性
Accelerator Intensity → GPU 硬件的属性    
也就是我们可以理解第一个是需要的，第二个是实际的


---

# 判断 Compute-bound 与 Memory-bound

判断一个操作的性能瓶颈，有两种等价的方法。

## 方法一：比较时间

### 如果计算时间更长

$$
T_{\text{compute}}
>
T_{\text{memory}}
$$

说明主要时间花在计算上，因此是：

```text
Compute-bound
```

### 如果显存搬运时间更长

$$
T_{\text{memory}}
>
T_{\text{compute}}
$$

说明主要时间花在搬运数据上，因此是：

```text
Memory-bound
```

---

## 方法二：比较两个 Intensity

比较操作的 Arithmetic Intensity和硬件的 Accelerator Intensity


### Arithmetic Intensity 更低

如果：

$$
I_{\text{op}}
<
I_{\text{accelerator}}
$$

说明操作每读取一个字节，只做了较少的计算，无法充分利用 GPU 的计算能力。

此时 GPU 的计算单元可能需要等待数据，因此是：

```text
Memory-bound
```

### Arithmetic Intensity 更高

如果：

$$
I_{\text{op}}
>
I_{\text{accelerator}}
$$

说明操作每读取一个字节，需要进行大量计算。

此时显存已经能够及时提供数据，主要瓶颈变成 GPU 的计算速度，因此是：

```text
Compute-bound
```


# 前向传播与反向传播

先看一个最简单的例子：

$$
h_2=h_1w_2
$$

假设：

$$
h_1=2,\qquad w_2=3
$$

前向传播得到：

$$
h_2=2\times3=6
$$

假设我们已经从后面的损失函数得到：

$$
h_2.grad
=
\frac{\partial L}{\partial h_2}
=
-4
$$

## 为什么反向传播要乘以 $w_2$

我们需要计算：

$$
h_1.grad
=
\frac{\partial L}{\partial h_1}
$$

因为：

$$
h_2=h_1w_2
$$

所以：

$$
\frac{\partial h_2}{\partial h_1}=w_2
$$

根据链式法则：

$$
\frac{\partial L}{\partial h_1}
=
\frac{\partial L}{\partial h_2}
\frac{\partial h_2}{\partial h_1}
$$

因此：

$$
h_1.grad
=
h_2.grad\times w_2
=
-4\times3
=
-12
$$

这里不是通过 $h_2$ 反推出 $h_1$，所以不是除以 $w_2$。反向传播计算的是：

> $h_1$ 改变一点时，Loss 会改变多少。

由于前向传播中 $h_1$ 的变化会被 $w_2$ 放大，所以梯度需要乘以 $w_2$。

## 为什么要计算两个梯度

对于：

$$
h_2=h_1w_2
$$

$h_1$ 和 $w_2$ 都会影响最终的 Loss，所以需要分别计算：

$$
\frac{\partial L}{\partial h_1}
\qquad\text{和}\qquad
\frac{\partial L}{\partial w_2}
$$

其中：

- $w_2.grad$ 用来更新当前层的权重；
- $h_1.grad$ 用来把梯度继续传给前一层。

因为：

$$
\frac{\partial h_2}{\partial w_2}=h_1
$$

所以：

$$
w_2.grad
=
h_2.grad\times h_1
=
-4\times2
=
-8
$$

可以记成：

```text
前向：
h2 = h1 × w2

反向：
h1.grad = h2.grad × w2
w2.grad = h2.grad × h1
```

# 扩展到矩阵乘法

前向传播：

```python
h2 = h1 @ w2
```

反向传播需要计算：

```python
h1_grad = h2_grad @ w2.T
w2_grad = h1.T @ h2_grad
```

前向传播只有一次主要的矩阵乘法，而反向传播需要两次：

1. 计算输入梯度 `h1_grad`；
2. 计算权重梯度 `w2_grad`。

假设一次矩阵乘法的计算量约为：

$$
2BDK
$$

那么：

$$
\text{Forward FLOPs}\approx2BDK
$$

$$
\text{Backward FLOPs}
\approx
2BDK+2BDK
=
4BDK
$$

因此：

$$
\text{Backward FLOPs}
\approx
2\times\text{Forward FLOPs}
$$

也就是说，在线性层中：

```text
反向传播的计算量约为前向传播的 2 倍
反向传播的耗时通常也约为前向传播的 2 倍
反向传播的吞吐速度则约为前向传播的 1/2
```
# 训练时的显存占用

训练时除了保存模型参数，还需要保存激活值、梯度和优化器状态。

这里使用一个简化模型：

```text
L：网络层数
D：每层的隐藏维度
B：一次前向传播中的样本数或 Token 数

假设每层只有一个形状为 [D, D] 的权重矩阵。
```

## Parameters

每层参数矩阵的形状为：

$$
[D,D]
$$

所以每层有：

$$
D^2
$$

个参数，$L$ 层共有：

$$
D^2L
$$

个参数。

假设参数使用 BF16，每个参数占 2 bytes：

$$
\text{Parameter Memory}
=
2D^2L
$$

## Activations

每层产生的激活值形状近似为：

$$
[B,D]
$$

每层有 $BD$ 个激活值，$L$ 层共有：

$$
BDL
$$

个激活值。

假设激活值使用 BF16，每个占 2 bytes：

$$
\text{Activation Memory}
=
2BDL
$$

训练时需要保存这些激活值，因为反向传播计算梯度时还会用到它们。

## Gradients

每个参数都需要一个对应的梯度，因此梯度数量同样为：

$$
D^2L
$$

假设梯度使用 FP32，每个梯度占 4 bytes：

$$
\text{Gradient Memory}
=
4D^2L
$$

这里的 4 来自 FP32 的 4 bytes，不是因为反向传播有两次矩阵乘法。

## Optimizer States

AdamW 会为每个参数保存两个状态：

```text
m：梯度的一阶矩
v：梯度的二阶矩
```

$m$ 和 $v$ 通常使用 FP32，每个分别占 4 bytes，所以每个参数对应：

$$
4+4=8\text{ bytes}
$$

因此：

$$
\text{Optimizer State Memory}
=
8D^2L
$$

## 总显存

将四部分相加：

$$
\text{Total Memory}
=
2D^2L
+
2BDL
+
4D^2L
+
8D^2L
$$

得到：

$$
\boxed{
\text{Total Memory}
=
14D^2L+2BDL
}
$$

其中：

```text
14D²L → 参数、梯度和优化器状态
2BDL  → 前向传播保存的激活值
```

这个公式只是简化估算，没有包括 Attention 中间结果、临时张量、CUDA 工作空间和显存碎片等内容。

---

# Activation Checkpointing

Activation Checkpointing 也叫：

```text
Gradient Checkpointing
Rematerialization
```

它的目的是减少训练时保存激活值所占用的显存。

## 普通训练

假设网络有 8 层，普通前向传播会保存每一层的激活值：

```text
输入
→ h1（保存）
→ h2（保存）
→ h3（保存）
→ h4（保存）
→ h5（保存）
→ h6（保存）
→ h7（保存）
→ h8（保存）
→ Loss
```

反向传播时，直接读取这些激活值来计算梯度。

这样反向传播速度较快，但需要保存所有层的激活值，显存占用较大。

## 只保留一部分激活值

Activation Checkpointing 不保存所有层的激活值，而是只选择部分层作为检查点。

例如，只保存：

```text
输入、h4、h8
```

前向传播变成：

```text
输入（保存）
→ h1（丢弃）
→ h2（丢弃）
→ h3（丢弃）
→ h4（保存）
→ h5（丢弃）
→ h6（丢弃）
→ h7（丢弃）
→ h8（保存）
→ Loss
```

这里的“只保留一部分”不是只保留某个张量的一部分元素，而是：

> 只保存某些层的完整激活值，其他层的激活值在前向传播完成后被释放。

## 反向传播时重新计算

反向传播到第 5～8 层时，需要使用 $h_5$、$h_6$、$h_7$，但这些激活值已经被丢弃。

因此从最近保存的检查点 $h_4$ 开始，重新执行一次前向传播：

```text
h4
→ 重新计算 h5
→ 重新计算 h6
→ 重新计算 h7
→ 重新计算 h8
→ 进行第 5～8 层的反向传播
```

随后再从输入重新计算 $h_1$～$h_4$，完成前面几层的反向传播。

## 为什么可以节省显存

普通训练需要保存所有 $L$ 层的激活值：

$$
\text{Activation Memory}
=
2BDL
$$

使用 Activation Checkpointing 后，只保存少数检查点，因此激活值显存会明显下降。

但是，被丢弃的激活值需要在反向传播时重新计算，所以计算量和训练时间会增加。

因此它的核心思想是：

```text
使用更多计算
换取更少显存
```

也就是：

> Trade memory for compute。

需要注意，Activation Checkpointing 主要减少的是：

$$
2BDL
$$

这一部分激活值显存。

它不会直接减少：

```text
参数显存
梯度显存
优化器状态显存
```

因此原来的总显存：

$$
14D^2L+2BDL
$$

使用 Activation Checkpointing 后，主要是其中的 $2BDL$ 会下降，而 $14D^2L$ 基本保持不变。
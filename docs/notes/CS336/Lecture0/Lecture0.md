---
title: "Lecture 0：概述"
---
# Tokenization

Tokenization 的作用是将人类能够阅读的文本，转换为模型能够处理的 **Token ID 序列**。

大致过程为：

```text
文本
→ UTF-8 字节序列
→ Token 序列
→ Token ID 序列
```

例如：

```text
the
```

首先会被转换为对应的 UTF-8 字节：

```text
116 104 101
```

如果使用 Byte-Pair Encoding，也就是 **BPE**，Tokenizer 会根据提前学习得到的合并规则，将相邻的字节或已有 Token 逐步合并。

例如：

```text
t + h → th
th + e → the
```

如果词表中规定：

```text
the → Token 256
```

那么最终编码结果就是：

```text
[256]
```

而不是：

```text
[116, 104, 101]
```

一个 BPE Tokenizer 通常包含两个重要部分：

* **Vocabulary**：记录每个 Token 对应的 Token ID。
* **Merge Rules**：记录相邻 Token 应该按照什么顺序合并。

Tokenizer 通常需要实现两个基本方法：

```python
tokenizer.encode(text)
tokenizer.decode(token_ids)
```

其中：

* `encode`：将文本转换为 Token ID。
* `decode`：将 Token ID 还原为文本。

Tokenizer 的一个重要指标是压缩比：

$$
\text{Compression Ratio} = \frac{\text{Number of Bytes}} {\text{Number of Tokens}}
$$

也就是：

$$
\text{byte/token}
$$

压缩比越高，表示相同文本需要的 Token 数量越少。

但是，词表并不是越大越好。词表过大会带来：

* Embedding 参数量增加。
* 输出层参数量增加。
* 部分 Token 出现次数过少，训练数据更加稀疏。
* 一些罕见 Token 很难得到充分训练。

因此，Tokenizer 需要在以下两个目标之间进行权衡：

```text
更高的压缩比
        与
更充分的 Token 训练
```

CS336 将 Tokenizer、模型结构和优化器作为从零训练语言模型的基础组成部分。

# Model Architecture

语言模型的基本数据流可以表示为：

```text
Token ID
→ Token Embedding
→ 多层模型模块
→ Final Norm
→ Linear Head
→ Logits
→ 下一个 Token 的概率分布
```

其中，`Logits` 是模型对词表中每一个 Token 给出的未归一化分数。

经过 Softmax 后，可以得到概率分布：

$$
P(x_{t+1}\mid x_1,\ldots,x_t) = \operatorname{Softmax}(\text{logits})
$$

## Transformer

现代语言模型通常使用 Transformer 架构。

一个常见的 Transformer Block 包括：

```text
输入
→ RMSNorm
→ Self-Attention
→ 残差连接
→ RMSNorm
→ MLP
→ 残差连接
→ 输出
```

其中：

* **Self-Attention**：让每个 Token 读取前面其他 Token 的信息。
* **MLP**：对每个 Token 的特征进行非线性变换。
* **RMSNorm**：稳定中间特征的数值范围。
* **Residual Connection**：让信息和梯度更容易通过深层网络传播。

## Self-Attention 的复杂度

假设序列长度为：

$$
n
$$

标准 Self-Attention 需要计算一个大小约为：

$$
n\times n
$$

的注意力分数矩阵。

因此，它关于序列长度的计算复杂度通常为：

$$
O(n^2)
$$

显存占用也会随着序列长度快速增加。

例如，序列长度从：

```text
4096 → 8192
```

增加了两倍，而注意力矩阵的大小大约会变为原来的：

$$
2^2=4
$$

倍。

FlashAttention 并没有改变标准注意力的数学结果，而是通过减少 GPU 高带宽显存和片上存储之间的数据读写，提高实际运行速度并降低中间显存占用。

为了处理更长的序列，可以研究其他模型结构。

## 状态空间模型

State Space Model，简称 **SSM**。

它不会显式构造完整的：

$$
n\times n
$$

注意力矩阵，而是通过一个不断更新的隐藏状态来压缩历史信息。

可以简单理解为：

```text
过去的隐藏状态
+
当前 Token
→
新的隐藏状态
```

其序列计算复杂度可以做到近似：

$$
O(n)
$$

Mamba 就是一种使用选择性状态空间机制的模型架构。

但是，SSM 需要将过去的信息压缩进有限大小的状态，因此它读取和保存历史信息的方式与 Attention 不同。

## 线性注意力机制

标准 Attention 可以写成：

$$
\operatorname{Attention}(Q,K,V) = \operatorname{Softmax}(QK^\top)V
$$

其中：

$$
QK^\top
$$

会产生一个：

$$
n\times n
$$

的矩阵。

线性注意力通过修改 Attention 的形式，并调整矩阵乘法顺序，避免显式构造完整的注意力矩阵。

它的复杂度可以从：

$$
O(n^2)
$$

降低到接近：

$$
O(n)
$$

但是，线性注意力通常不再与标准 Softmax Attention 完全相同，可能会损失一部分表达能力。

## 稠密 MLP

在普通 Transformer 中，每一层都会包含一个 MLP。

稠密 MLP 的特点是：

```text
所有 Token
→ 使用同一套 MLP 参数
→ 所有 MLP 参数都参与计算
```

例如：

$$
\operatorname{MLP}(x) = W_{\text{down}} \left( \operatorname{SiLU}(W_{\text{gate}}x) \odot W_{\text{up}}x \right)
$$

对于每一个 Token，模型都会使用相同的：

* `gate_proj`
* `up_proj`
* `down_proj`

因此它被称为 **Dense MLP**。

## 混合专家

Mixture of Experts，简称 **MoE**。

MoE 会将一个 MLP 替换为多个不同的 MLP，也就是多个专家：

```text
Expert 1
Expert 2
Expert 3
...
Expert N
```

模型还会增加一个 Router：

```text
Token
→ Router
→ 选择最合适的一个或几个专家
→ 专家进行计算
```

例如，一个模型有 8 个专家，但每个 Token 只选择其中 2 个：

```text
8 个总专家
2 个激活专家
```

这样可以让模型拥有大量总参数，但每个 Token 只激活一小部分参数。

因此，MoE 的核心特点是：

```text
总参数量很大
但每次计算只激活部分参数
```

MoE 并不会自动减少模型的总参数量或者显存占用，它主要减少的是每个 Token 实际参与计算的参数量。

MoE 还会带来一些新的问题：

* Router 可能总是选择少数几个专家。
* 不同专家的负载可能不均衡。
* 多 GPU 训练时存在额外的通信开销。
* 训练过程可能更加不稳定。

Switch Transformer 使用稀疏路由，让不同输入激活不同的专家参数。

# Training

语言模型训练的基本过程为：

```text
1. 从数据集中取出一批 Token
2. 模型进行前向传播
3. 计算预测结果和正确答案之间的 Loss
4. 进行反向传播，计算梯度
5. Optimizer 根据梯度更新参数
6. 重复以上过程
```

## Loss Function

语言模型通常使用 **Next-Token Prediction**。

假设输入是：

```text
我 喜欢 人工 智能
```

模型需要完成：

```text
输入：我
预测：喜欢

输入：我 喜欢
预测：人工

输入：我 喜欢 人工
预测：智能
```

训练时通常使用交叉熵损失：

$$
\mathcal{L} = -\frac{1}{T} \sum_{t=1}^{T} \log P(x_t\mid x_1,\ldots,x_{t-1})
$$

模型给正确 Token 的概率越高，Loss 越小。

语言模型的训练目标就是不断降低这个 Loss。

## Optimizer

Optimizer 的作用是根据梯度更新模型参数。

最基础的梯度下降可以写成：

$$
\theta_{t+1} = \theta_t-\eta g_t
$$

其中：

* $\theta_t$：当前模型参数。
* $g_t$：当前梯度。
* $\eta$：学习率。

实际训练大语言模型时，通常会使用更加复杂的优化器。

### AdamW

AdamW 会维护梯度的一阶矩和二阶矩。

一阶矩可以理解为梯度的移动平均：

$$
m_t = \beta_1m_{t-1} + (1-\beta_1)g_t
$$

二阶矩可以理解为梯度平方的移动平均：

$$
v_t = \beta_2v_{t-1} + (1-\beta_2)g_t^2
$$

然后根据：

$$
\frac{m_t}{\sqrt{v_t}+\epsilon}
$$

调整不同参数的更新幅度。

AdamW 还将 Weight Decay 与梯度更新分离。

AdamW 的优点：

* 使用广泛。
* 训练相对稳定。
* 对不同参数自适应地调整更新幅度。
* 有大量成熟的训练经验。

缺点：

* 每个参数通常需要保存一阶矩和二阶矩。
* Optimizer State 会占用大量显存。

### Muon

Muon 全称可以理解为：

```text
MomentUm Orthogonalized by Newton-Schulz
```

Muon 主要用于神经网络内部的二维权重矩阵。

它首先计算类似 Momentum SGD 的更新矩阵，然后通过 Newton-Schulz 迭代，对更新矩阵进行近似正交化。

可以简单理解为：

```text
普通梯度更新
→ 调整更新矩阵的几何方向
→ 得到更加均衡的矩阵更新
```

Muon 通常不会用于模型中的所有参数。

常见做法是：

```text
Transformer 内部的二维权重矩阵 → Muon

Embedding、输出层、Bias、Norm 参数 → AdamW
```

因此，Muon 通常需要与 AdamW 配合使用，而不是简单地完全替换 AdamW。

### SOAP

SOAP 的全称是：

```text
Shampoo with Adam in the Preconditioner's Eigenbasis
```

SOAP 可以理解为将 Shampoo 的矩阵预条件思想与 Adam 结合。

它会：

```text
1. 分析梯度矩阵的结构
2. 找到一个更加合适的坐标空间
3. 在这个空间中执行类似 Adam 的更新
4. 再将更新转换回原来的空间
```

与 AdamW 只对每个参数元素分别维护统计量不同，SOAP 会利用权重矩阵不同方向之间的相关性。

优点：

* 在部分大 Batch 训练任务中，可以减少达到目标 Loss 所需的训练步数。
* 能利用矩阵参数的结构信息。

缺点：

* 实现更加复杂。
* 需要额外进行矩阵分解或预条件计算。
* 可能带来更多计算、显存和工程开销。

SOAP 论文将其解释为在 Shampoo 预条件器的特征基中运行 Adam。

## Initialization

Initialization 决定模型参数在训练开始时的初始值。

初始化非常重要。

如果初始参数过大，可能导致：

* 激活值过大。
* 梯度爆炸。
* Loss 不稳定。

如果初始参数过小，可能导致：

* 激活值逐层衰减。
* 梯度消失。
* 模型学习速度过慢。

### Xavier Initialization

Xavier Initialization 会根据输入维度和输出维度设置参数的方差。

常见形式为：

$$
\operatorname{Var}(W) = \frac{2}{n_{\text{in}}+n_{\text{out}}}
$$

它的目标是让前向传播中的激活值和反向传播中的梯度，在不同网络层之间保持相对稳定。

Xavier 初始化最初就是为改善深层神经网络中激活和梯度传播困难而提出的。

### muP

$\mu P$ 的全称是：

```text
Maximal Update Parameterization
```

需要注意：

> $\mu P$ 不只是一个普通的初始化方法，而是一整套参数化和缩放规则。

当模型宽度改变时，普通参数化下最合适的：

* 学习率
* 初始化尺度
* 参数更新尺度

也可能发生变化。

$\mu P$ 的目标是让不同宽度模型的训练动态尽可能保持一致。

这样就可以：

```text
先在小模型上寻找超参数
→ 将超参数迁移到更大的模型
→ 减少大模型超参数搜索成本
```

因此，$\mu P$ 的核心作用是：

```text
Hyperparameter Transfer
```

也就是超参数跨模型规模迁移。

## Learning Rate

Learning Rate，也就是学习率，控制每次参数更新的步长。

学习率过大：

```text
参数更新过猛
→ Loss 振荡
→ 甚至训练发散
```

学习率过小：

```text
参数更新太慢
→ 训练时间增加
→ 可能长期无法达到较好的结果
```

语言模型训练通常使用学习率调度。

一个常见策略是：

```text
Warmup
→ 保持或达到最大学习率
→ 逐渐衰减
```

### Warmup

训练开始时，模型参数和 Optimizer State 都不稳定。

因此，先从较小的学习率开始，然后逐渐增大：

$$
\eta_t = \eta_{\max} \frac{t}{T_{\text{warmup}}}
$$

### Cosine Decay

Warmup 结束后，可以使用余弦衰减逐渐降低学习率：

$$
\eta_t = \eta_{\min} + \frac{1}{2} (\eta_{\max}-\eta_{\min}) \left( 1+ \cos \left( \pi\frac{t-T_{\text{warmup}}} {T-T_{\text{warmup}}} \right) \right)
$$

训练前期使用较大学习率快速学习，训练后期使用较小学习率进行更加精细的调整。

## Regularization

Regularization，也就是正则化，用于减少过拟合并提高训练稳定性。

常见方法包括：

### Weight Decay

对过大的参数进行惩罚，让参数不会无限增大。

可以简单理解为：

```text
每次更新参数时
顺便让参数稍微向 0 收缩
```

### Dropout

训练时随机将一部分激活值设置为 0，避免模型过度依赖某些固定特征。

不过，在拥有大量训练数据的大语言模型预训练中，Dropout 不一定总是必要。

### Gradient Clipping

当梯度范数过大时，将其限制在一定范围内。

例如：

$$
g \leftarrow g \cdot \min \left( 1, \frac{c}{\lVert g\rVert} \right)
$$

其中 $c$ 是允许的最大梯度范数。

Gradient Clipping 主要用于避免梯度爆炸，提高训练稳定性。

## Batch Size

Batch Size 表示一次参数更新使用多少个训练样本或者 Token。

例如：

```text
Batch Size = 32
```

表示模型处理 32 个样本后，进行一次参数更新。

对于语言模型，更常用的是全局 Token Batch Size：

$$
\text{Global Batch Tokens} = \text{Number of GPUs} \times \text{Batch per GPU} \times \text{Sequence Length} \times \text{Gradient Accumulation Steps}
$$

较大的 Batch Size：

* 梯度估计更加稳定。
* GPU 并行效率通常更高。
* 需要更多显存。
* 可能需要相应调大学习率。

较小的 Batch Size：

* 梯度噪声更大。
* 单步显存占用更低。
* 参数更新次数更多。
* GPU 利用率可能较低。

如果显存无法容纳较大的 Batch，可以使用 Gradient Accumulation：

```text
连续计算多个小 Batch 的梯度
→ 暂时不更新参数
→ 累积完成后统一更新
```

这样可以模拟更大的 Batch Size。

# Kernels

正确的单数形式是：

```text
Kernel
```

复数形式是：

```text
Kernels
```

GPU Kernel 是一段在 GPU 上并行执行的函数。

例如，神经网络中的以下操作最终都可能由一个或多个 GPU Kernel 完成：

* Matrix Multiplication
* Softmax
* RMSNorm
* Activation Function
* Attention
* 参数更新

在 PyTorch 中写：

```python
y = torch.matmul(x, w)
```

虽然只是一行 Python 代码，但底层通常会调用 CUDA、cuBLAS 或其他 GPU Kernel。

## 为什么需要自己写 Kernel

高级框架提供的操作不一定总能针对特定模型达到最高效率。

模型运行速度不仅取决于进行了多少次浮点运算，还取决于：

* 数据从显存读取了多少次。
* 中间结果写回显存多少次。
* GPU 线程是否被充分利用。
* Kernel 启动次数。
* 不同操作之间是否能够融合。

例如：

```text
RMSNorm
→ Linear
→ Activation
```

如果分别执行，可能需要多次：

```text
读取显存
→ 执行计算
→ 写回显存
```

如果将它们融合为一个 Kernel，就可以：

```text
读取一次数据
→ 连续完成多个操作
→ 最后写回一次
```

这种方法叫做：

```text
Kernel Fusion
```

自己编写 Kernel 的主要目标包括：

* 减少显存读写。
* 减少中间 Tensor。
* 减少 Kernel Launch。
* 提高并行度。
* 更好地利用 Tensor Core。
* 针对特定形状优化计算。

常见的 Kernel 编写工具包括：

* CUDA
* Triton
* CUTLASS
* CuTe

但是，自己编写 Kernel 还需要保证：

* 数学结果正确。
* 数值误差可以接受。
* 不同输入形状都能运行。
* 不会出现越界访问。
* 反向传播结果正确。

因此，优化 Kernel 通常需要同时比较：

```text
Correctness
Speed
Memory Usage
Numerical Stability
```

# Inference

Inference 指模型训练完成后，使用模型生成结果的过程。

自回归语言模型一次通常只生成一个 Token：

```text
输入 Token
→ 模型预测下一个 Token
→ 将新 Token 加入输入
→ 再预测下一个 Token
→ 不断重复
```

例如：

```text
我
→ 喜欢

我 喜欢
→ 人工

我 喜欢 人工
→ 智能
```

## Prefill

Prefill 阶段处理用户一次性输入的完整 Prompt。

例如：

```text
请解释一下 Transformer 的工作原理
```

模型可以并行处理这些输入 Token，并生成对应的 Key 和 Value。

Prefill 阶段通常：

* 并行度较高。
* 计算量较大。
* 更容易充分利用 GPU。
* 主要受到计算能力影响。

## Decode

Decode 阶段每次只生成一个新 Token。

生成一个 Token 后，再将它作为下一步的输入：

```text
Token 1
→ Token 2
→ Token 3
→ Token 4
```

Decode 阶段通常：

* 每次处理的 Token 数量很少。
* 并行度较低。
* 需要反复读取模型权重和 KV Cache。
* 更容易受到显存带宽影响。

## KV Cache

在自回归生成过程中，前面 Token 对应的 Key 和 Value 不需要每次重新计算。

因此，可以将它们保存起来：

```text
过去 Token 的 Key、Value
→ KV Cache
```

生成新 Token 时，只需要计算新 Token 对应的：

```text
Query
Key
Value
```

然后让新的 Query 与 KV Cache 中保存的 Key 和 Value 进行 Attention。

KV Cache 可以显著减少重复计算，但会占用额外显存。

KV Cache 的大小通常会随着以下因素增加：

* Batch Size
* Sequence Length
* Number of Layers
* Number of KV Heads
* Head Dimension
* 数据精度

## Inference 的评价指标

### Latency

完成一次请求需要多长时间。

常见指标包括：

* **TTFT**：Time to First Token，生成第一个 Token 所需时间。
* **TPOT**：Time per Output Token，生成后续每个 Token 所需时间。

### Throughput

单位时间内能够处理多少 Token：

$$
\text{Throughput} = \frac{\text{Number of Tokens}} {\text{Time}}
$$

通常使用：

```text
tokens/second
```

### Memory Usage

推理显存主要包括：

```text
模型参数
+
KV Cache
+
激活值
+
临时计算空间
```

## 常见推理优化方法

* **Quantization**：使用 INT8、INT4 或 FP8 等低精度表示模型。
* **Continuous Batching**：动态地将不同用户的请求组合起来。
* **Paged KV Cache**：更加灵活地管理 KV Cache 显存。
* **Speculative Decoding**：使用小模型提前预测，再由大模型验证。
* **Tensor Parallelism**：将一层模型拆分到多个 GPU。
* **Pipeline Parallelism**：将不同模型层放到不同 GPU。
* **Kernel Fusion**：减少显存访问和 Kernel 启动。
* **FlashAttention**：降低 Attention 的显存读写开销。

训练主要关心：

```text
需要多少时间和计算量把模型训练好
```

推理主要关心：

```text
模型训练完成后
能否以更低延迟、更高吞吐量和更低成本生成结果
```

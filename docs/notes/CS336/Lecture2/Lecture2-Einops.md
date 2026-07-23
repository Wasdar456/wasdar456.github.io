---
title : Lecture 2:Tensor&Einops
---

# Tensor(张量)
包含矩阵和向量，可以推广到任意维度

## 张量需要的空间
1. float32（FP32/单精度）：一个符号位，8个指数位，23个小数位
eg：    
我们构建一个4*8的矩阵，32位数的大小是4字节（byte）总共是128bytes    
这个更加占用内存  
2. float16（FP16）：一个符号位，5个指数位，10个小数位
3. bfloat16（BF16）：一个符号位，8个指数位，7个小数位    
很多时候范围比精度更重要一点    
虽然BF16是比较中恒的选择，但是大家还是更多用混合精度
指数运算会保留到FP32
4. fp8有两个版本：
 - 一个是4个指数位
 - 一个是5个指数位
5. fp4（Nemotron是在fp4上面训练的）当然会有缩放因子，范围会好很多，但是还会有稀疏问题
# Einops

`einops` 是一个用于处理张量维度的 Python 库，可以配合 PyTorch、NumPy、TensorFlow 和 JAX 使用。

它主要用于：

- 交换张量维度；
- 合并或拆分维度；
- 重复张量；
- 对指定维度进行聚合；
- 更直观地表示张量乘法。

常用函数包括：

```python
from einops import rearrange, reduce, repeat, einsum
```

---

## 1. rearrange：重新排列张量

### 假设一个图像张量形状是

```text
[B, C, H, W]
```

其中：

- `B`：batch size，批量大小；
- `C`：channel，通道数；
- `H`：height，图像高度；
- `W`：width，图像宽度。

现在想把它转换成：

```text
[B, H, W, C]
```

### 普通 PyTorch 写法

```python
x = x.permute(0, 2, 3, 1)
```

这里的数字表示原张量维度的位置：

```text
原来：[B, C, H, W]
位置：[0, 1, 2, 3]

新的顺序：[0, 2, 3, 1]
结果：[B, H, W, C]
```

### einops 写法

```python
from einops import rearrange

x = rearrange(x, "b c h w -> b h w c")
```

其中：

```text
b c h w -> b h w c
```

表示：

```text
输入维度：b c h w
输出维度：b h w c
```

einops 的优点是可以直接看到每个维度的含义，不需要记忆 `0、2、3、1` 分别代表哪个维度。

---

## 2. 使用括号合并维度

假设图像特征的形状是：

```text
[B, C, H, W]
```

现在希望把图像的高度和宽度合并，转换成 Transformer 使用的 token 序列：

```python
x = rearrange(x, "b c h w -> b (h w) c")
```

转换过程为：

```text
[B, C, H, W]
        ↓
[B, H × W, C]
```

例如：

```text
输入：[2, 768, 14, 14]
输出：[2, 196, 768]
```

因为：

$$
14 \times 14 = 196
$$

这里的：

```text
(h w)
```

表示将 `h` 和 `w` 合并为一个维度。

---

## 3. 拆分多头注意力维度

假设张量形状是：

```text
[B, N, D]
```

其中：

- `B`：batch size；
- `N`：token 数量；
- `D`：隐藏维度。

多头注意力会把隐藏维度拆成：

\[
D=H\times D_h
\]

其中：

- `H`：注意力头数量；
- \(D_h\)：每个注意力头的维度。

einops 写法：

```python
q = rearrange(
    q,
    "b n (h d) -> b h n d",
    h=num_heads
)
```

例如：

```text
输入：[B, 196, 768]
注意力头数量：12
```

因为：

$$
768 \div 12 = 64
$$

所以输出形状是：

```text
[B, 12, 196, 64]
```

注意力计算结束后，可以重新合并：

```python
q = rearrange(q, "b h n d -> b n (h d)")
```

输出重新变成：

```text
[B, 196, 768]
```

---

## 4. einsum：张量乘法

`einsum` 可以通过维度名称描述矩阵乘法或更加复杂的张量运算。

### 示例1

```python
import torch
from einops import einsum

def einops_einsum():
    x = torch.ones(3, 4)
    y = torch.ones(4, 3)

    # 普通矩阵乘法
    z_old = x @ y

    # einops 写法
    z_new = einsum(
        x,
        y,
        "seq1 hidden, hidden seq2 -> seq1 seq2"
    )

    print(z_old)
    print(z_new)
    print(z_new.shape)
```

#### 张量形状
```text
x：seq1 hidden
y：hidden seq2
z：seq1 seq2
```

因此：

```text
seq1 = 3
hidden = 4
seq2 = 3
```

也就是：

```text
x.shape = [seq1, hidden] = [3, 4]
y.shape = [hidden, seq2] = [4, 3]
z.shape = [seq1, seq2] = [3, 3]
```

#### 表达式的含义

```python
"seq1 hidden, hidden seq2 -> seq1 seq2"
```

可以分解为：

```text
seq1 hidden    hidden seq2    ->    seq1 seq2
     x              y                  z
```

`hidden` 出现在输入中，但没有出现在输出中，因此需要沿着 `hidden` 维度进行乘法并求和。

对应数学公式：

$$
z_{i,j}
=
\sum_{k=1}^{K} x_{i,k} y_{k,j}
$$

这就是普通矩阵乘法。

### 示例2
我们看一个更加complicate的例子
```python
x = torch.ones(2,3,4)# batch seq1 hidden
y = torch.ones(2,3,4)# batch seq2 hidden

z = x @ y.transpose(-2,-1)#batch seq1 seq2 这边是默认将最后两个维度作为矩阵维度，将前面的维度作为 batch 维度
z_new = einsum(
        x,
        y,
        "batch seq1 hidden, batch seq2 hidden -> batch seq1 seq2"
    )#我们用命名就实现了转置
z_new = einsum(
        x,
        y,
        "... seq1 hidden, ... seq2 hidden -> ... seq1 seq2"
    )#当然也可以用省略号代替
```
## 5. einsum 中的维度名称

`seq1`、`seq2` 和 `hidden` 都只是人为定义的维度名称，并不是 Python 中预先定义的关键字。

例如下面两种写法完全等价：

```python
z = einsum(
    x,
    y,
    "seq1 hidden, hidden seq2 -> seq1 seq2"
)
```

```python
z = einsum(
    x,
    y,
    "a b, b c -> a c"
)
```

## 6. Reduce

`einops.reduce` 用于在改变张量维度结构的同时，对某些维度进行归约操作。

```python
from einops import reduce
import torch

x = torch.ones(2, 3, 4)  # batch, seq, hidden
````

其中：

```text
x.shape = [2, 3, 4]
        = [batch, seq, hidden]
```

### 对 hidden 维求和

PyTorch 的写法：

```python
y = x.sum(dim=-1)
```

Einops 的写法：

```python
y = reduce(x, "... hidden -> ...", "sum")
```

其中：

```text
... hidden -> ...
```

表示：

* `...` 代表前面的所有维度；
* `hidden` 出现在输入中；
* `hidden` 没有出现在输出中；
* 因此需要消除 `hidden` 维度；
* `"sum"` 表示通过求和消除该维度。

输入形状：

```text
[batch, seq, hidden]
= [2, 3, 4]
```

输出形状：

```text
[batch, seq]
= [2, 3]
```

因为 `x` 中的元素全部为 1，所以每四个元素求和：

$$
1+1+1+1=4
$$

最终：

```python
print(y)
```

输出：

```text
tensor([
    [4., 4., 4.],
    [4., 4., 4.]
])
```


### 1. 求和：`sum`

```python
y = reduce(x, "... hidden -> ...", "sum")
````

等价于：

```python
y = x.sum(dim=-1)
```

每组结果为：

$$
1+1+1+1=4
$$

所以：

```text
y.shape = [2, 3]
y 中每个元素都是 4
```

---

### 2. 最大值：`max`

```python
y = reduce(x, "... hidden -> ...", "max")
```

等价于：

```python
y = x.max(dim=-1).values
```

因为每组是：

```text
[1, 1, 1, 1]
```

最大值为：

$$
\max(1,1,1,1)=1
$$

所以结果中的每个元素都是 `1`。

需要注意，PyTorch 的：

```python
x.max(dim=-1)
```

会同时返回最大值和最大值的位置；而 `einops.reduce(..., "max")` 只返回最大值。

---

### 3. 最小值：`min`

```python
y = reduce(x, "... hidden -> ...", "min")
```

等价于：

```python
y = x.min(dim=-1).values
```

计算：

$$
\min(1,1,1,1)=1
$$

所以每个结果也是 `1`。

---

### 4. 平均值：`mean`

```python
y = reduce(x, "... hidden -> ...", "mean")
```

等价于：

```python
y = x.mean(dim=-1)
```

计算：

$$
\frac{1+1+1+1}{4}=1
$$

所以每个结果都是 `1`。

---

### 5. 连乘：`prod`

```python
y = reduce(x, "... hidden -> ...", "prod")
```

等价于：

```python
y = x.prod(dim=-1)
```

计算：

$$
1\times1\times1\times1=1
$$

所以每个结果都是 `1`。

---

### 6. 逻辑判断：`any` 和 `all`

这两个操作主要用于布尔张量。

```python
x_bool = torch.tensor([
    [True, False],
    [True, True]
])
```

只要某个元素为真：

```python
y = reduce(x_bool, "batch hidden -> batch", "any")
```

结果：

```text
[True, True]
```

所有元素都必须为真：

```python
y = reduce(x_bool, "batch hidden -> batch", "all")
```

结果：

```text
[False, True]
```

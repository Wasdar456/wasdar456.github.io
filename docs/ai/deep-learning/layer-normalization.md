---
title: LayerNorm 前向与反向推导
course: 深度学习
chapter: 归一化
status: reviewing
updated: 2026-07-21
source_kind: audited-study-note
sources:
  - https://arxiv.org/abs/1607.06450
  - https://pytorch.org/docs/stable/generated/torch.nn.LayerNorm.html
---

# LayerNorm 前向与反向推导

## 学习目标

明确 LayerNorm 在哪些轴上计算均值和方差；手算前向标准化；从链式法则推导对输入、缩放参数 $\gamma$ 和平移参数 $\beta$ 的梯度；用零和性质与数值梯度检查推导；理解 LayerNorm 与 BatchNorm 的统计对象不同。

## 前置知识

需要均值、方差、向量微分、链式法则和广播。设单个归一化组含 $D$ 个元素。深度学习张量可有 batch、序列、通道等轴，LayerNorm 的 `normalized_shape` 决定最后若干轴；下面先对一个向量推导，再把所有非归一化轴视为独立组。

## 核心概念与符号表

对 $x=(x_1,\ldots,x_D)$：

$$
\mu=\frac1D\sum_{i=1}^D x_i,
\qquad
\sigma^2=\frac1D\sum_{i=1}^D(x_i-\mu)^2,
$$

$$
\hat x_i=\frac{x_i-\mu}{\sqrt{\sigma^2+\epsilon}},
\qquad
y_i=\gamma_i\hat x_i+\beta_i.
$$

这里使用总体方差（分母 $D$），与 PyTorch `LayerNorm` 的 biased variance 对应。$\epsilon$ 用于数值稳定。$\gamma,\beta$ 的形状与 normalized shape 一致，通常对所有 batch 和 token 共享。

直觉上，减均值移除共同偏移，除标准差移除共同尺度；仿射参数再让网络按特征恢复有用的尺度与偏移。LayerNorm 不要求运行时维护跨 batch 的移动统计，因此训练和推理使用同一当前样本统计。

## 前向推导与张量形状

若输入形状为 `[B, T, H]` 且 `normalized_shape=H`，每个 `(b,t)` 位置独立在 $H$ 个隐藏维上计算统计量：

- `mean`, `var`: `[B, T, 1]`，保留维度便于广播；
- `x_hat`, `y`: `[B, T, H]`；
- `gamma`, `beta`: `[H]`，广播到 batch 与 token。

```mermaid
graph LR
  A[输入张量] --> B[计算统计量]
  A --> C[中心化]
  B --> C
  C --> D[标准差缩放]
  D --> E[仿射变换]
  E --> F[输出张量]
```

如果误沿 batch 轴归一化，就变成依赖其他样本的统计，模型行为与 LayerNorm 根本不同。

## 反向公式推导

记上游梯度 $d_i=\partial L/\partial y_i$，先吸收仿射缩放：

$$
g_i=\frac{\partial L}{\partial \hat x_i}=d_i\gamma_i,
\qquad s=\sqrt{\sigma^2+\epsilon}.
$$

参数梯度在所有独立归一化组上求和：

$$
\frac{\partial L}{\partial\beta_i}=\sum_{groups}d_i,
\qquad
\frac{\partial L}{\partial\gamma_i}=\sum_{groups}d_i\hat x_i.
$$

输入梯度可从计算图分三路。令 $c_i=x_i-\mu$。第一路是 $\hat x_i=c_i/s$ 的直接项 $g_i/s$；第二路来自方差；第三路来自均值。逐项化简后得到紧凑式：

$$
\boxed{
\frac{\partial L}{\partial x_i}
=\frac{1}{Ds}
\left[
Dg_i-\sum_{j=1}^Dg_j-\hat x_i\sum_{j=1}^Dg_j\hat x_j
\right]
}
$$

其向量形式为

$$
dx=\frac1s\left(g-\operatorname{mean}(g)-\hat x\operatorname{mean}(g\odot\hat x)\right).
$$

为什么形式中出现两个投影？标准化对统一平移不敏感，所以梯度必须去除常数方向 $\mathbf1$；对统一缩放近似不敏感，所以还要去除 $\hat x$ 方向。由公式可立即验证 $\sum_i dx_i=0$。当 $\epsilon=0$ 时还满足 $\sum_i dx_i\hat x_i=0$；$\epsilon>0$ 时第二个关系会有小的修正。

### 链式法则的展开路径

方差对输入的导数可简化为

$$
\frac{\partial\sigma^2}{\partial x_i}=\frac{2}{D}(x_i-\mu),
$$

因为 $\sum_j(x_j-\mu)=0$ 使均值导数产生的交叉项抵消。再有

$$
\frac{\partial s^{-1}}{\partial \sigma^2}=-\frac12(\sigma^2+\epsilon)^{-3/2}.
$$

把所有 $g_j$ 经过 $s^{-1}$、方差与均值的路径相加，正好得到盒中公式。这比为每个 $x_i,x_j$ 写 Jacobian 更紧凑，也便于向量化实现。

## 完整数值例子

取两行输入，先令 $\gamma=1,\beta=0,\epsilon=0$ 便于手算：

$$
X=\begin{bmatrix}1&2&3\\2&4&4\end{bmatrix}.
$$

第一行 $\mu_1=2$，$\sigma_1^2=2/3$，因此

$$
\hat x^{(1)}\approx[-1.224745,0,1.224745].
$$

第二行 $\mu_2=10/3$，偏差为 $[-4/3,2/3,2/3]$，方差为

$$
\sigma_2^2=\frac{(16/9)+(4/9)+(4/9)}3=\frac89,
$$

所以

$$
\hat x^{(2)}\approx[-1.414214,0.707107,0.707107].
$$

两行都满足均值约为 0、平方均值约为 1。这个检查能发现旧手算中常见的第二行数值错误。实际实现必须保留 $\epsilon$，因此平方均值会略小于 1。

用 NumPy 核对：

```python
import numpy as np

x = np.array([[1., 2., 3.], [2., 4., 4.]])
mu = x.mean(axis=-1, keepdims=True)
var = ((x - mu) ** 2).mean(axis=-1, keepdims=True)
x_hat = (x - mu) / np.sqrt(var)
np.testing.assert_allclose(x_hat.mean(-1), 0.0, atol=1e-12)
np.testing.assert_allclose((x_hat**2).mean(-1), 1.0, atol=1e-12)
```

反向检查可随机生成 $x,\gamma,\beta,dout$，用上式计算解析梯度，再对每个输入做中心差分

$$
\frac{L(x_i+h)-L(x_i-h)}{2h}
$$

比较相对误差。`float64` 和 $h\approx10^{-5}$ 通常更适合梯度检查；过小 $h$ 会被浮点舍入淹没。

## 常见错误、适用条件与反例

1. **归一化轴错误。** `[B,T,H]` 的普通 Transformer LayerNorm 沿 $H$，不是沿 $B$ 或 $T$。
2. **使用无偏方差。** 框架实现通常使用分母 $D$；手算用 $D-1$ 会与结果不符。
3. **把 $dout$ 直接代入输入梯度。** 必须先乘 $\gamma$ 得到 $g=dout\odot\gamma$。
4. **忘记 $\gamma,\beta$ 的求和轴。** 参数对 batch/token 共享，梯度要在这些轴上累积。
5. **认为归一化后方差严格为 1。** 有 $\epsilon$ 时是 $\sigma^2/(\sigma^2+\epsilon)<1$。
6. **常数输入会除零。** $\epsilon$ 使输出有限；此时信号主要由 $\beta$ 决定，输入梯度也受 $\epsilon$ 强烈控制。
7. **把 LayerNorm 等同于训练稳定保证。** Pre-LN、Post-LN、残差尺度、初始化和优化器共同影响深层网络训练。

## 与前后章节的关系

本节依赖反向传播，向后连接 Transformer 的 Pre-LN/Post-LN、RMSNorm 与混合精度稳定性。RMSNorm 不减均值，只按均方根缩放，因此其不变性和反向投影方向不同，不能直接复用本节所有直觉。

## 自测题与答案提示

1. `[2,4,8,16]` 输入，`normalized_shape=(8,16)` 时每组有多少元素？提示：128，每个前两维索引独立一组。
2. 为什么 $\sum_i dx_i=0$？提示：输出对所有输入同时加常数不变，梯度与常数方向正交。
3. 若 `elementwise_affine=False`，哪些梯度消失？提示：没有可学习的 $\gamma,\beta$，但输入梯度仍通过标准化传播。
4. 常数向量的标准化输出是什么？提示：在标准公式中为全零，再经仿射得到 $\beta$。

## 参考资料

- Ba, Kiros & Hinton, *Layer Normalization*。
- PyTorch `torch.nn.LayerNorm` 文档：normalized shape、biased variance 与 affine 参数语义。

## 校对信息

最后校对：2026-07-21。掌握状态：复习中。两行前向数值、方差分母、输入梯度公式与张量轴已重新核验；后续补充自动微分对照测试。

Tomasi-Kanade法による3次元復元
==============================

こんにちは，いしたーです．最近は[株式会社DeNA](https://dena.com/jp/)で3次元復元関連のアルバイトをしています．

今回は3次元復元の古典的な手法であるTomasi-Kanade法の解説と実装をしていきます．コードは[GitHub]()にあります．


## Tomasi-Kanade法とは

3次元復元を行う手法

- 全ての視点から全てのランドマーク集合が観測されている
- 違う視点から観測されたランドマーク同士がの関連付け(Data association)が済んでいる

という前提でSfMを実行することができる．

## できないこと

- スケールは復元できない
- 若干歪んでしまう


## やること

今回は例としてコンピュータビジョン界の人気者であるこのうさぎさんを3次元復元してみます．


![うさぎさん画像]()

このうさぎさんはすでに3次元なのですが，これを仮想的にカメラで撮影し，得られた2次元の画像(点群)のみからうさぎさんを3次元復元してみます．

### 例

うさぎさんの写真を何十枚か撮影してみて

![]()
![]()
![]()
![]()

これにTomasi-Kanade法を適用すると

こんなふうにうさぎさんを3次元復元することができます

![回転する3次元のうさぎさんのgif]()


# 手法

ではさっそく手法を解説していきます．

## 基本的な考え方

__物体を3次元復元してみてそれを再度カメラに投影(再投影)したときに，実際に撮影された点と再投影された点の差がなるべく小さくなるよう，3次元の点の位置とカメラの位置を調整する．__

![図](カメラで得た2Dの点群 -> 3次元復元構築 -> 再投影)


うさぎさんを構成する3次元の点$\mathbf{X}_{j},\,j=1,...,n$があるとします．
これを$i$番目のカメラに投影するするとき，その像を

$\hat{\mathbf{x}}^{i}_{j} = M^{i}\mathbf{X}_{j} + \mathbf{t}^{i}$

と表すことにします．

違う方向から何枚も写真を撮っているので視点が複数あることに注意してください．視点が$m$個あるとき，$i=1,...,m$です．

$M^{i}$は$2 \times 3$の行列です．
これは何を表しているかというと，復元したい点$\mathbf{X}_{j}$は3次元，その像$\hat{\mathbf{x}}^{i}_{j}$は2次元なので，その間の関係を表すためにおいた行列が$M^{i}$というだけのことです． 

$\mathbf{t}^{i}$は2次元のベクトルです．もし$\mathbf{X}_{j} = (0, 0, 0)^{\hat}$だとしても，その像が$(0, 0)^{\hat}$の点に投影されるとは限らないので，その「ずれ」を表しているのがこのベクトル$\mathbf{t}^{i}$です．ずれの大きさはカメラごとに異なるので$i$がついています．

![オフセットの説明]()

以上より，

* 実際に観測された2次元の点 $\mathbf{x}^{i}_{j}$
* 物体を3次元復元たものを再度カメラに投影して得られた点 $\hat{\mathbf{x}}^{i}_{j}$

の差

$$
\sum_{i=1}^{m} \sum_{j=1}^{n} ||\mathbf{x}^{i}_{j}-\hat{\mathbf{x}}^{i}_{j}||^2
$$

がなるべく近くなるような$\mathbf{X}_{j}$，$M^{i}$，$\mathbf{t}^i$の組み合わせを求める問題だということができる．


## 解き方
### $\mathbf{t}^i$の消去
$\mathbf{X}_{j}$，$M^{i}$，$\mathbf{t}^i$も全て不定だと未知変数が多すぎて解くのが大変なので，まず$\mathbf{t}^i$を消去します．


誤差を最小化する $\mathbf{t}^{i}$ は次の式で求められます．

$$\frac{\partial}{\partial \mathbf{t}^{i}} \underset{kj}{\sum}
|| \mathbf{x}^{k}\_{j} - (M^{k}\mathbf{X}\_{j} + \mathbf{t}^{k}) ||^2
\= \mathbf{0}$$

変形していく

$$\begin{aligned}
\begin{align}
\frac{\partial}{\partial \mathbf{t}^{i}} \underset{kj}{\sum}
|| \mathbf{x}^{k}\_{j} - (M^{k}\mathbf{X}\_{j} + \mathbf{t}^{k}) ||^2
&=
\frac{\partial}{\partial \mathbf{t}^{i}} \underset{kj}{\sum}
(\mathbf{x}^{k}\_{j} - (M^{k}\mathbf{X}\_{j} + \mathbf{t}^{k}))^{\top}
(\mathbf{x}^{k}\_{j} - (M^{k}\mathbf{X}\_{j} + \mathbf{t}^{k})) \\\\
&=
\frac{\partial}{\partial \mathbf{t}^{i}} \underset{kj}{\sum}
[
    - 2(\mathbf{x}^{k}\_{j})^{\top} \mathbf{t}^{k}
    + 2(M^{k}\mathbf{X}\_{j})^{\top} \mathbf{t}^{k}
    + (\mathbf{t}^{k})^{\top} \mathbf{t}^{k}
] \\\\
&=
\frac{\partial}{\partial \mathbf{t}^{i}} \underset{j}{\sum}
[
    - 2(\mathbf{x}^{i}\_{j})^{\top} \mathbf{t}^{i}
    + 2(M^{i}\mathbf{X}\_{j})^{\top} \mathbf{t}^{i}
    + (\mathbf{t}^{i})^{\top} \mathbf{t}^{i}
] \\\\
&=
\underset{j}{\sum}
[
    - 2 \mathbf{x}^{i}\_{j}
    + 2 M^{i}\mathbf{X}\_{j}
    + 2 \mathbf{t}^{i}
] \\\\
&= \mathbf{0}
\end{align}
\end{aligned}$$

$$\begin{aligned}
\begin{align}
n\mathbf{t}^{i} &=
\underset{j}{\sum}
[
    \mathbf{x}^{i}\_{j} - M^{i}\mathbf{X}\_{j}
] \\\\
\mathbf{t}^{i} &=
\frac{1}{n}
\underset{j}{\sum}
[
    \mathbf{x}^{i}\_{j} - M^{i}\mathbf{X}\_{j}
] \\\\
\end{align}
\end{aligned}$$

ここで

$$\begin{aligned}
\begin{align}
\overline{\mathbf{x}^{i}} &:=
\frac{1}{n} \underset{j}{\sum} \mathbf{x}^{i}\_{j} \\\\
\overline{\mathbf{X}} &:=
\frac{1}{n} \underset{j}{\sum} \mathbf{X}\_{j}
\end{align}
\end{aligned}$$

とおくと、 $\mathbf{t}^{i}$ は

$$\mathbf{t}^{i} =
\overline{\mathbf{x}^{i}} - M^{i}\overline{\mathbf{X}}$$

と表すことができます．
これをもとの誤差の式に代入すると 

$$\underset{ij}{\sum}
|| \mathbf{x}^{i}\_{j} - (M^{i}\mathbf{X}\_{j} + \mathbf{t}^{i}) ||^2
\=
\underset{ij}{\sum}
|| \mathbf{x}^{i}\_{j}
- (M^{i}\mathbf{X}\_{j}
+ \overline{\mathbf{x}^{i}}
- M^{i}\overline{\mathbf{X}}) ||^2$$

となり，$\mathbf{t}^{i}$ を消去することができました．

さて，$\hat{\mathbf{x}}^{i}_{j}$は$\mathbf{x}^{i}_{j}$に近い値を取らなければならないため，$\mathbf{X}_{j}$と$M^{i}$のうちどちらか片方が定まるともう片方も定まりますが，現時点ではどちらもまだ定まっていません．
つまり$\mathbf{X}_{j}$は任意の値をとることが可能なので，$\overline{\mathbf{X}}$も任意の値に設定することができます．

計算を簡単にするため、

$$\overline{\mathbf{X}} := \mathbf{0}$$

と定めると、

$$\begin{aligned}
\begin{align}
\underset{ij}{\sum}
|| \mathbf{x}^{i}\_{j} - \hat{\mathbf{x}}^{i}\_{j} ||^2
&=
\underset{ij}{\sum}
|| \mathbf{x}^{i}\_{j}
- (M^{i}\mathbf{X}\_{j}
+ \overline{\mathbf{x}^{i}}) ||^2 \\\\
&=
\underset{ij}{\sum}
|| \mathbf{x}^{i}\_{j}
- \overline{\mathbf{x}^{i}}
- M^{i}\mathbf{X}\_{j} ||^2
\end{align}
\end{aligned}$$

さらに $\mathbf{x}^{i}\_{j}$ を

$$\mathbf{x}^{i}\_{j} \leftarrow
\mathbf{x}^{i}\_{j} - \overline{\mathbf{x}^{i}}$$

というふうに上書きすると，誤差は


$$\underset{ij}{\sum}
|| \mathbf{x}^{i}\_{j} - (M^{i}\mathbf{X}\_{j} + \mathbf{t}^{i}) ||^2
\=
\underset{ij}{\sum}
|| \mathbf{x}^{i}\_{j} - M^{i}\mathbf{X}\_{j} ||^2$$

というかたちにまで簡略化することができます．

さて，不定な変数が$\mathbf{X}_{j}$と$M^{i}$のみになりました．
愚直に勾配法などを用いて解を求めてもよいのですが，$\mathbf{X}_{j}$も$M^{i}$も不定なので解を求めるのはとても大変です．
そこで特異値分解を利用して一気に解の候補を出してしまおうというのがTomasi-Kanade法の戦略です．

### SVDによる3次元座標の計算
では実際に$\mathbf{X}_{j}$と$M^{i}$を求めていきましょう．

Tomasi-Kanade法では measurement matrix という行列をつくり，これを特異値分解(SVD)することで$\mathbf{X}_{j}$と$M^{i}$の候補を定めます．

### Measurement matrix

measurement matrix といっても簡単で，単にカメラによって得られた2次元の座標を並べて行列にしたものです．

$$\begin{aligned}
W =
\begin{bmatrix}
\mathbf{x}^{1}\_{1} & \dots & \mathbf{x}^{1}\_{j} & \dots & \mathbf{x}^{1}\_{n} \\\\
\vdots & \ddots & & & \vdots \\\\
\mathbf{x}^{i}\_{1} & & \mathbf{x}^{i}\_{j} & & \mathbf{x}^{i}\_{n} \\\\
\vdots & & & \ddots & \vdots \\\\
\mathbf{x}^{m}\_{1} & \dots & \mathbf{x}^{m}\_{j} & \dots & \mathbf{x}^{m}\_{n} \\\\
\end{bmatrix}
\end{aligned}$$

それぞれの$\mathbf{x}^{i}\_{j}$は2次元なので，$W$は$2m \times 3$の行列です．

推定値$\hat{\mathbf{x}}^{i}\_{j}$も同様に並べて行列にします．

$$
\begin{aligned}
\hat{W} =
\begin{bmatrix}
\hat{\mathbf{x}}^{1}\_{1} & \dots & \hat{\mathbf{x}}^{1}\_{j} & \dots & \hat{\mathbf{x}}^{1}\_{n} \\\\
\vdots & \ddots & & & \vdots \\\\
\hat{\mathbf{x}}^{i}\_{1} & & \hat{\mathbf{x}}^{i}\_{j} & & \hat{\mathbf{x}}^{i}\_{n} \\\\
\vdots & & & \ddots & \vdots \\\\
\hat{\mathbf{x}}^{m}\_{1} & \dots & \hat{\mathbf{x}}^{m}\_{j} & \dots & \hat{\mathbf{x}}^{m}\_{n} \\\\
\end{bmatrix}
\end{aligned}
$$

すると$\hat{\mathbf{X}^{i}_{j} = M^{i}\mathbf{X}\_{j}$より，$\hat{W}$は

$$
\begin{aligned}
\hat{W}
\=
M\mathbf{X}
\=
\begin{bmatrix}
    M^{1} \\\\
    \vdots \\\\
    M^{i} \\\\
    \vdots \\\\
    M^{m}
\end{bmatrix}
\begin{bmatrix}
    \mathbf{X}^{1} &
    \dots &
    \mathbf{X}^{j} &
    \dots &
    \mathbf{X}^{n}
\end{bmatrix}
\end{aligned}
$$

と表すことができます．

### 特異値分解による解の候補の計算

$W$を特異値分解してみましょう．

$W$ は $2m \times n$ の行列なので，

$$
\begin{aligned}
\begin{align}
U &\in \mathbb{R}^{2m \times 2m} \\\\
D &\in \mathbb{R}^{2m \times n} \\\\
V^{\top} &\in \mathbb{R}^{n \times n}
\end{align}
\end{aligned}
$$

という3つの行列に分解することができます．

さて，

* $M^{i}$は$2 \times 3$の行列
* $\mathbf{X}\_{j}$は3次元のベクトル

なので，$\mathbf{x}^{i}_{j}$が$\hat{\mathbf{X}^{i}_{j} = M^{i}\mathbf{X}\_{j}$というモデルに従うのであれば，$W$のランクは3になります．すなわち，$D$の対角成分のうち左上の3つ以外は全て0になります．

実際にはぴったりこのモデルに従うわけではありませんし，ノイズ等もあるので，ランクはぴったり3にはなりません．
しかし$D$の対角成分のうち左上から数えて4つ目以降は，3つ目までと比べるとかなり小さい値になります．

![Dの対角成分の絶対値]()

よって$D$の対角成分の4つ目以降と，関連する$U$と$V^{\top}$の要素を削除してしまいます．

$$\begin{aligned}
\begin{align}
U &\in \mathbb{R}^{2m \times 3} \\\\
D &\in \mathbb{R}^{3 \times 3} \\\\
V^{\top} &\in \mathbb{R}^{3 \times n}
\end{align}
\end{aligned}$$

![SVD.png](https://qiita-image-store.s3.amazonaws.com/0/46932/37c8b6a2-5c8d-df65-8340-385a8dc31737.png)

すると

$$
\begin{aligned}
\begin{align}
\hat{M} &= U D \\\\
\hat{\mathbf{X}} &= V^{\top}
\end{align}
\end{aligned}$$

とおけば $\hat{W} = \hat{M}\hat{\mathbf{X}}$ を満たす $\hat{M}$ と $\hat{\mathbf{X}}$ を定めることができます．


## 問題点

### 解に一意性がない

$\hat{W}$ を $\hat{W} = U D V^{\top}$ というふうに分解し， $\hat{W} = \hat{M}\hat{\mathbf{X}}$ から

$$\begin{aligned}
\begin{align}
\hat{M} &= U D \\\\
\hat{\mathbf{X}} &= V^{\top}
\end{align}
\end{aligned}$$

とおきましたが，この $\hat{M}$ と $\hat{\mathbf{X}}$ の決め方には一意性がありません．

例えば，

__(A)__

$$\begin{aligned}
\begin{align}
\hat{M} &= U \\\\
\hat{\mathbf{X}} &= D V^{\top}
\end{align}
\end{aligned}$$

としたり，

__(B)__
$$\begin{aligned}
\begin{align}
\hat{M} &= U D^{1/2} \\\\
\hat{\mathbf{X}} &= D^{1/2} V^{\top}
\end{align}
\end{aligned}$$

とおいたりしても$W = M\mathbf{X}$を満たすことができます．

![Aのときの点群X]()

![Bのときの点群X]()

さらには任意のアフィン行列 $Q \in \mathbb{R}^{3 \times 3}$ を使って　

$$\begin{aligned}
\begin{align}
\hat{M} &= U D Q \\\\
\hat{\mathbf{X}} &= Q^{-1} V^{\top}
\end{align}
\end{aligned}$$

としても $\hat{W} = \hat{M}\hat{\mathbf{X}}$ が成り立ってしてしまいます．

さて，どの解が正しいのでしょうか？


## 解を定める方法
なんの制約もないと$M$も$\mathbf{X}$も定めることができないので，何らかの制約を入れてやる必要があります．

#### 制約

$$
M^{i} = \begin{bmatrix}
    {\mathbf{m}^{i}_{1}}^{\top}\\
    {\mathbf{m}^{i}_{2}}^{\top}
\end{bmatrix}
$$

と表すとき，$\mathbf{m}^{\top}_{1}$と$\mathbf{m}^{\top}_{2}$は直交し，

$$
\begin{align}
\mathbf{m}^{\top}_{1} \mathbf{m}_{1} &= 0  \\
\mathbf{m}^{\top}_{2} \mathbf{m}_{2} &= 0  \\
\mathbf{m}^{\top}_{1} \mathbf{m}_{2} &= $\mathbf{m}^{\top}_{2} \mathbf{m}_{1} = 1
\end{align}
$$

を満たす．

^[footnote]．

この制約を満たすように$M^{i}$を定めてやります．

とりあえず

$$
\begin{align}
\hat{M} &= U D  \\
\hat{\mathbf{X}} &= V^{\top}  \\
M^{i} &= \hat{M}^{i}Q  \\
\mathbf{X}_{j} = Q^{-1}\hat{\mathbf{X}}_{j} 
\end{align}
$$

とおき，

$$
\begin{align}
E(Q)
&=
\sum\_{i=1}^{m} || M^{i}{M^{i}}^{\top} - I ||^{2}\_{F} \\\\
&=
\sum\_{i=1}^{m} || {\hat{M}^{i}}QQ^{\top}{\hat{M}^{i}}^{\top} - I ||^{2}\_{F}
\end{align}
$$

を最小化するような$Q$を求めます．
自分で勾配を導出して$E(Q)$を最小化しても良いのですが，Chainerなら勾配の導出も最小化も全てやってくれるのでここは任せてしまいましょう．

$E(Q)$を最小化する$Q$が求まれば，あとは

$$
M^{i} &= \hat{M}^{i}Q  \\
\mathbf{X}_{j} = Q^{-1}\hat{\mathbf{X}}_{j} 
$$

により，最適な$M$と$\mathbf{X}$を定めることができます．

# 欠点
## 手法を実行できる環境が非常に限られている

Tomasi-Kanade法を実行する過程でMotion matrixという行列を作りましたが，これを作ることができるケースは非常に限られています．
というのも，

* 全ての視点から復元したい全ての点が観測されていなければならない
* 別々の視点から観測された点同士の対応づけがされていなければならない

という非常に厳しい条件を満たさなければならないためです．

## 復元結果の歪みを完全に除去するのは難しい

これは全ての$M^{i}$について[上記制約](#### 制約)を満たすことが難しいためです．
行列$M$は「特異値分解によって得た行列のうち必要な部分だけ切り取る」というわりと荒い操作によって得られたものなので，最適な$Q$を求めることが難しく，復元結果がゆがんでしまいます．

# まとめ


[footnote] $M^{i}$はカメラの内部パラメータ$K \in \mathbb{R}^{2 \ times 3}$と姿勢を表現する行列$R^{i} \in \mathrm{SO}(3)$を用いて$M^{i} = R^{i}K$と表されます．この$K$の中身によって制約が変わってきます．今回は[正投影モデル](https://en.wikipedia.org/wiki/Orthographic_projection)を採用しているので$K^{i} \= \begin{bmatrix} 1 & 0 & 0 \\\\ 0 & 1 & 0 \end{bmatrix}$です.


# 青龙脚本

用青龙脚本，自动摘取gihub release,并解压到阿里云服务器上

实现个人博客的同步。

# python

fork from https://github.com/Sitoi/dailycheckin

可以参考其说明 https://sitoi.github.io/dailycheckin/

# 本地使用

## 安装 miniconda3（如果有python3环境，可以不装）

https://docs.conda.io/projects/miniconda/en/latest/

conda create -n qinglong python=3.9
conda activate qinglong
conda deactivate

## 运行


python start.py --include blog 

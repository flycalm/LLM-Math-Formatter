Markdown Math Formula Converter
A Python tool specialized in converting mathematical formula text output by Large Language Models (LLMs) like Gemini into standard LaTeX-formatted Markdown.
一个专门用于将Gemini等大语言模型输出的数学公式文本转换为标准LaTeX格式Markdown的Python工具。

## 注意
在vscode中使用 渲染插件选择markdown preview enhanced 插件的设置中选择使用katex
![image](https://github.com/user-attachments/assets/aed97a45-f468-4b76-ab55-a99cd2ad1ce6)

## 主要功能

- 自动识别并格式化数学公式
- 将普通文本格式的数学符号转换为LaTeX格式
- 智能处理以下数学表达式：
  - 上下标 (如 `x_i`, `x^2`)
  - 求和符号 (如 `Σ(i=1 to n)`)
  - 矩阵表示
  - 特殊符号 (如 `≠`, `×`)
- 自动区分行内公式和块级公式
- 保持代码块内容不被转换

## 使用场景

主要用于处理以下场景：
1. 将Gemini等AI模型输出的数学公式文本转换为标准Markdown
2. 处理包含大量数学公式的文档
3. 批量转换非标准数学公式为LaTeX格式

## 安装依赖

```bash
pip install regex


使用方法
将AI输出的文本保存为.md文件
修改程序中的输入输出文件名：

input_file = '你的输入文件.md'
output_file = '输出文件.md'

运行程序：
python 自动转换.py

注意事项
输入文件需要使用UTF-8编码
程序会自动处理文件中的缩进
代码块中的内容不会被转换
建议在转换后检查重要公式的显示效果

License
MIT

贡献
欢迎提交Issue和Pull Request来完善这个工具。

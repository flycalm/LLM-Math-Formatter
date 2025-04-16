import re
import regex # Using the more powerful regex library

# format_subscript and format_superscript remain the same
def format_subscript(match):
    var = match.group(1); sub = match.group(2)
    if len(sub) > 1 or not sub.isalnum():
         if not (sub.startswith('{') and sub.endswith('}')): return f"{var}_{{{sub}}}"
         else: return f"{var}_{sub}"
    else: return f"{var}_{sub}"

def format_superscript(match):
    var = match.group(1); sup = match.group(2)
    if sup == 'T': return f"{var}^{sup}"
    # 确保^2直接附加到变量上，而不是分离的
    if sup.isdigit() and len(sup) == 1:
        return f"{var}^{sup}"
    if len(sup) > 1 and not (sup.startswith('{') and sup.endswith('}')): 
        return f"{var}^{{{sup}}}"
    else: 
        return f"{var}^{sup}"

def clean_math_content(content):
    content = content.replace("...", r"\dots")
    # 替换所有'*'为空格
    content = content.replace("*", " ")
    
    # 先处理下标问题 - 确保q_ij变成q_{ij}
    content = regex.sub(r'([a-zA-Z])_([a-zA-Z]+)([0-9]*)', r'\1_{\2\3}', content)
    
    # 然后再应用其他格式化
    if not content.startswith('\\sum') and not content.startswith('\\int'):
         content = sub_pattern_math.sub(format_subscript, content)
         content = sup_pattern_math.sub(format_superscript, content)
    
    # 修复类似\(x_i\)^\(2 = x_i\)的模式
    content = regex.sub(r'\\\(([^)]+)\\\)\^\\\(([^)]+)\\\)', r'\(\1^\2\)', content)

    # 其余部分保持不变
    content = regex.sub(r'\s*([=+\-/<>])\s*', r' \1 ', content).strip()
    content = content.replace('\\neq', ' \\neq ')
    content = content.strip()
    content = regex.sub(r'\s+', ' ', content)
    return content

sub_pattern_math = regex.compile(r"\b([a-zA-Z]'?)_(\{.*?\}|[\w]+)")
sup_pattern_math = regex.compile(r"([a-zA-Z]'?|\])\^(\{.*?\}|T|\w+)")

def correct_markdown_math(text):
    # --- Pre-processing (using \neq) ---
    text = regex.sub(r"`([^`]+?)`", r"\1", text)
    text = text.replace("≠", " \\neq ")
    text = text.replace("!=", " \\neq ")
    text = regex.sub(r'\s*([=+\-*/<>])\s*', r' \1 ', text) # Include * here
    text = regex.sub(r'\s*\\neq\s*', r' \\neq ', text)
    text = regex.sub(r'\s*,\s*', r', ', text)
    text = regex.sub(r"\b(n)\s*x\s*(n)\b", r"\(n \times n\)", text) # 修改为单层转义

    # --- Convert Σ structures BEFORE line processing ---
    text = regex.sub(r"Σ\s*\(\s*([ijkln])\s*=\s*1\s+(?:to|TO)\s+([a-zA-Z0-9]+)\s*\)", r"\\sum_{\1=1}^{\2}", text)
    text = regex.sub(r"Σ\s*\(\s*([ijkln])\s+\\neq\s+([ijkln])\s*\)", r"\\sum_{\1 \\neq \2}", text)
    text = regex.sub(r"Σ\s*\(\s*([ijkln])\s*([<>])\s*([ijkln])\s*\)", r"\\sum_{\1 \2 \3}", text)
    text = text.replace("Σ", "\\sum")

    # --- Process Lines ---
    lines = text.splitlines()
    processed_lines = []
    in_code_block = False
    for line in lines:
        # 在处理行之前添加
        if line.startswith("    ") and not line.startswith("    ```"):
            # 只有在不是代码块的情况下移除前导空格
            if not (processed_lines and processed_lines[-1].strip().startswith("```")):
                line = line.lstrip()  # 移除所有前导空格
        # ... (code block skipping) ...
        if line.strip().startswith("```"):
            in_code_block = not in_code_block; processed_lines.append(line); continue
        if in_code_block:
            processed_lines.append(line); continue

        stripped_line = line.strip()

        # ... (block formula detection/handling - keep $$) ...
        is_block_formula = False
        if regex.match(r"^\s*(?:y\s*=|\\sum|\\int|[A-Z]'?\s*=)", stripped_line) and not stripped_line.endswith(':'):
             if regex.search(r"=\s*(\[\[.*?\]\]|\\begin\{pmatrix\})", stripped_line): is_block_formula = True
             elif regex.search(r"\\sum.*\\sum|\\frac|\\int", stripped_line): is_block_formula = True
             elif stripped_line.startswith("y =") and len(stripped_line) > 20: is_block_formula = True
             elif stripped_line.startswith("\\sum") and len(stripped_line) > 20: is_block_formula = True

        if is_block_formula: # Block formula handling
            def replace_matrix(match): # Matrix logic
                var_name = match.group(1); matrix_str = match.group(2)
                try:
                    rows = eval(matrix_str.replace('[','(').replace(']',')'))
                    latex_matrix = " \\\\\n".join([" & ".join(map(str, row)) for row in rows])
                    return f"{var_name} = \\begin{{pmatrix}}\n{latex_matrix}\n\\end{{pmatrix}}"
                except: return f"{var_name} = {matrix_str}"
            processed_block = regex.sub(r"([A-Z]'?)\s*=\s*(\[\[.*?\]\])", replace_matrix, stripped_line)
            cleaned_block = clean_math_content(processed_block)
            processed_lines.append(f"$$ {cleaned_block} $$") # Keep $$ for block
            continue

        # --- Handle Inline Formulas ---
        temp_line = line
        processed_parts = []
        last_end = 0
        # Using v5/v6 math seed pattern - includes operators like '*'
        math_seed_pattern = regex.compile(
            r"(\\sum(?:_\{[^{}]*?\}|_[\w])?(?:\^\{[^{}]*?\}|^\w)?)"
            r"|(\\int(?:_\{[^{}]*?\}|_[\w])?(?:\^\{[^{}]*?\}|^\w)?)"
            r"|(\\(?:neq|not=|dots|times|cdot|frac\{[^{}]*?\}\{[^{}]*?\}) )"
            r"|([a-zA-Z]'?_\{[^{}]*?\})"
            r"|([a-zA-Z]'?_[\w]+)"
            r"|(([a-zA-Z]'?|\])\^\{[^{}]*?\})"
            r"|(([a-zA-Z]'?|\])\^(?:T|\w+))"
            r"|(\b[ijklnxyQ][\'_]?\w*\b)"
            r"|(\d+(?:\.\d+)?)"
            r"|([=+\-*/<>])"  # Matches operators including *
            r"|(\([^\)]*\)|\{[^}]*\}|\[[^\]]*\])"
        )
        potential_matches = list(math_seed_pattern.finditer(temp_line))

        # *** MODIFIED Merging Logic ***
        merged_blocks = []
        i = 0
        while i < len(potential_matches):
            current_match = potential_matches[i]; start, end = current_match.span(); j = i + 1
            while j < len(potential_matches):
                next_match = potential_matches[j]; next_start, next_end = next_match.span()
                intervening_text = temp_line[end:next_start]
                # --- Allow merging across whitespace OR common math operators ---
                stripped_intervening = intervening_text.strip()
                if stripped_intervening == "" or stripped_intervening in ['*', '+', '-', '/', '=']: # Merge if space or operator
                    end = next_end # Extend current block
                    j += 1
                else:
                    break # Stop merging if intervening text is something else
                # --- End Modification ---
            merged_blocks.append((start, end)); i = j
        # *** End MODIFIED Merging Logic ***

        # Wrapping logic (using \( \) as per v6)
        for start, end in merged_blocks:
             temp_text_before = temp_line[last_end:start]
             # Basic check if already inside delimiters
             open_inline = temp_text_before.rfind('\\('); close_inline = temp_text_before.rfind('\\)')
             open_block = temp_text_before.rfind('$$')
             currently_open = False
             if open_inline > close_inline and open_inline > open_block: currently_open = True

             if not currently_open:
                 math_content = temp_line[start:end]
                 # Clean the *entire* merged content block
                 cleaned_content = clean_math_content(math_content)

                 # Avoid wrapping trivial/word content
                 if cleaned_content.isdigit() and not ((start > 0 and temp_line[start-1]=='(') or (end < len(temp_line) and temp_line[end]==')')):
                      processed_parts.append(temp_line[last_end:start]); processed_parts.append(cleaned_content)
                 elif cleaned_content.lower() in ["is", "in", "or", "and", "to", "a", "the", "if", "for", "with"]:
                      processed_parts.append(temp_line[last_end:start]); processed_parts.append(cleaned_content)
                 elif cleaned_content:
                      processed_parts.append(temp_line[last_end:start])
                      # Wrap the entire cleaned block in ONE pair of delimiters
                      processed_parts.append(f"\\({cleaned_content}\\)")
                 else:
                      processed_parts.append(temp_line[last_end:start])
                 last_end = end
             else: # Already inside math, append as is
                 processed_parts.append(temp_line[last_end:end])
                 last_end = end

        processed_parts.append(temp_line[last_end:])
        processed_line = "".join(processed_parts)

        # Post-processing cleanup for \( \)
        processed_line = regex.sub(r"\\\)\s*\\\(", " ", processed_line) # Merge adjacent
        processed_line = regex.sub(r"\\\(\s*\\\)", "", processed_line) # Remove empty

        processed_lines.append(processed_line)

    return "\n".join(processed_lines)

def post_process_fixes(text):
    """对已转换文档进行最终修复"""
    # 修复多余反斜杠问题
    text = regex.sub(r'\\\\(\([^)]*\)\\)', r'\\\1', text)
    
    # 修复错误的指数格式
    text = regex.sub(r'\\\(([^)]+)\\\)\^\\\(([^)]+)\\\)', r'\(\1^\2\)', text)
    
    # 修复缺少花括号的下标
    text = regex.sub(r'\\sum_([a-z]) ', r'\\sum_{\1} ', text)
    text = regex.sub(r'q_([a-z][a-z])', r'q_{\1}', text)
    
    # 添加这行：修复行内公式中Sigma下标显示位置问题
    text = regex.sub(r'\\\(\\sum', r'\\(\\displaystyle\\sum', text)
    
    # 移除多余换行前的缩进
    text = regex.sub(r'\n\s{4}(?!\s)', r'\n', text)
    
    return text

# --- Input/Output Files ---
input_file = '4.15.md'
output_file = '4.15_converted_v7_merged.md' # New output filename

# --- Read/Execute/Save ---
try:
    with open(input_file, 'r', encoding='utf-8') as f: input_text = f.read()
except FileNotFoundError: print(f"错误: 找不到输入文件 '{input_file}'"); exit(1)
except Exception as e: print(f"读取文件时发生错误: {str(e)}"); exit(1)

corrected_text = correct_markdown_math(input_text)
corrected_text = post_process_fixes(corrected_text)

try:
    with open(output_file, 'w', encoding='utf-8') as f: f.write(corrected_text)
    print(f"转换完成! 输出文件已保存为: {output_file}")
except Exception as e: print(f"保存文件时发生错误: {str(e)}"); exit(1)
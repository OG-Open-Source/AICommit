# 常用的規則：

**檔案編碼：** 使用 UTF-8 作為檔案編碼。

# 縮排：

- 使用 4 個空格作為縮排。

```python
# Good
def example_function():
    pass

# Bad
def example_function():
  pass
```

# 空格和運算符：

在運算符周圍放置一個空格，但不要在括號內做這樣的事情。

```python
# Good
result = x + y

# Bad
result = x+y
```

在以下情況下避免使用多餘的空格：
### 緊鄰圓括號、方括號或大括號內：

```python
# Good
spam(ham[1], {eggs: 2})

# bad
spam( ham[ 1 ], { eggs: 2 } )
```

### 緊接在逗號、分號或冒號之前：

```python
# Good
if x == 4: print(x, y); x, y = y, x

# bad
if x == 4 : print(x , y) ; x , y = y , x
```

### 如果使用具有不同優先權的運算符，請考慮在優先權最低的運算子周圍新增空格：

```python
# Good
i = i + 1
submitted += 1
x = x*2 - 1
hypot2 = x*x + y*y
c = (a+b) * (a-b)

# bad
i=i+1
submitted +=1
x = x * 2 - 1
hypot2 = x * x + y * y
c = (a + b) * (a - b)
```

# 行長度：

- 一行的長度應該不超過 79 個字符，可以使用反斜杠 `\` 進行行連接。
- 如果一行過長，可以在括號內的表達式、花括號內的字典、方括號內的列表等地方進行換行。
- **使用反斜杠進行行連接：**

```python
long_line = "This is a very long line that exceeds the recommended length " \
            "of 79 characters. Using a backslash allows us to break it " \
            "into multiple lines for better readability."
```

### 在括號內進行換行：

```python
result = some_function_that_takes_arguments(
    'argument1', 'argument2', 'argument3',
    'argument4', 'argument5', 'argument6'
)
```

### 在字典（花括號內）進行換行：

```python
my_dict = {
    'key1': 'value1',
    'key2': 'value2',
    'key3': 'value3',
}
```

### 在列表（方括號內）進行換行：

```python
my_list = [
    'item1', 'item2', 'item3',
    'item4', 'item5', 'item6',
]
```

### 二元運算子的換行位置：

```python
# Good
income = (gross_wages
          + taxable_interest
          + (dividends - qualified_dividends)
          - ira_deduction
          - student_loan_interest)
          
# bad
income = (gross_wages +
          taxable_interest +
          (dividends - qualified_dividends) -
          ira_deduction -
          student_loan_interest)
```

# 空行：
- 在不同函式或類之間應當有兩行空行。
- 在函式或類內部，根據邏輯結構添加適當的空行以提高可讀性。

```python
# Good
def function1():
    pass

def function2():
    pass

class ExampleClass:
    def __init__(self):
        pass

# Bad
def function1():
    pass
def function2():
    pass

class ExampleClass:
    def __init__(self):
        pass
```

# import：

- 單獨導入應當放在文件頂部，並按照標準順序進行導入。
- 避免使用通用導入 `import *`。
- 每行 import 只導入一個模組
- 每個分組之間用一行空行分隔 1. 標準庫 2. 相關第三方庫 3. 自己的模組
- 推薦使用絕對導入

```python
# Good
import module1
import module2

# Bad
from module1 import *

#推薦使用絕對導入
import mypkg.sibling
from mypkg import sibling
from mypkg.sibling import example
```

# 命名規則：

- 函式、變數和屬性使用小寫字母，單詞之間使用底線 `_` 分隔（snake_case）。
- 類使用大寫字母開頭的單詞（CapWords，或稱 CamelCase）。
- 切勿使用字元`“l”`（小寫字母 el）、`“O”`（大寫字母 oh）或`“I”`（大寫字母 eye）作為單字元變數名稱。
在某些字體中，這些字元與數字 **1 和 0 無法區分**。想要使用 **“l”** 時，請改用 **“L”**

```python
# Good
def example_function():
    pass

class ExampleClass:
    pass

# Bad
def ExampleFunction():
    pass

class example_class:
    pass
```

與None的比較，用is， not is。不要用 == 與!=。

```python
# Good:
variable = None

if variable is None:
    print("變數是 None")
else:
    print("變數不是 None")

# Bad:​
if variable == None:
    print("變數是 None")
else:
    print("變數不是 None")
```

另外 is not順序也很重要。雖然這兩個表達式在功能上相同，但前者更具可讀性

```python
# Good:
if foo is not None:

# Bad:
if not foo is None:
```

# 檢查序列（字串、列表、元組）是否為空值時

使用 `if not seq` 或 `if seq` 更加 **Pythonic**，更符合**慣例**，並提高了代碼的**可讀性**。**避免**不必要的**函數調用**，使代碼**更簡潔**。

```python
# Good
if not seq:
if seq:

# Bad
if len(seq):
if not len(seq):
```


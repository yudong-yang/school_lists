# School List

一个用于查询和管理高考大学信息的 Python 项目。当前版本提供轻量 CLI 和 SQLite
存储，后续可以继续扩展为 Web API、后台管理系统或数据采集管道。

## 功能

- 新增大学信息
- 按名称、省份、办学层次等条件查询
- 查看大学详情
- SQLite 本地持久化

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
school-list init
school-list add "清华大学" --province 北京 --city 北京 --level 本科 --type 综合 --website https://www.tsinghua.edu.cn
school-list list --province 北京
```

如果不安装包，也可以直接运行：

```bash
PYTHONPATH=src python3 -m school_list.cli --db data/schools.db init
```

## 数据字段

大学基础信息当前包含：

- `name`: 学校名称
- `province`: 所在省份
- `city`: 所在城市
- `level`: 办学层次，例如本科、专科
- `school_type`: 学校类型，例如综合、理工、师范、医药
- `ownership`: 公办、民办、中外合作办学等
- `website`: 官方网站
- `notes`: 备注

## 开发

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
pytest
ruff check .
```

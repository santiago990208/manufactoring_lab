from rich.table import Table

data = {
    "name": "John Doe",
    "age": 30,
    "city": "New York"
}

table = Table(title="User Information")
table.add_column("Key", style="cyan")
table.add_column("Value", style="yellow")
for key, value in data.items():
    table.add_row(key, str(value))
print(table)

# What is Flask?

Flask is a python micro web back end framework. In translation we could say:

- Flask does not force rule on us.
- We decide the folder structure.
- We decide how authentication works.
- It is lightweight, fast, perfet for learning backend fundamentals.

## Setting up Flask

### 1️⃣ Setup our project folder

```bash
mkdir project_name
cd project_name
```

Now we need to setup virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2️⃣ Install Flask

```bash
pip install flask
```

### 3️⃣ Creating our first flask app (The foundation brick)

create a file called `app.py`

```bash
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
  return "Hello, Flask!"

if __name__ == "__main__":
  app.run(debug=True)
```
Execute it by:

```bash
python3 app.py
```

open browser:

```bash
http://127.0.0.1:5000
```

The result will be like:

<img width="1921" height="1046" alt="image" src="https://github.com/user-attachments/assets/a6f14b3f-1f01-4924-8c3f-b2290d40fe6b" />

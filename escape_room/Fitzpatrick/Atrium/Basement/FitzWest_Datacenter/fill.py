import random

def make_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

def make_yaml(ip, name):
    content = f"""
hooks:
  getattr: &hide_not_match
    - condition: 
        not:
          file_content_matches:
            path: search.me
            expected_content: "\\\\s*{name}\\\\s*"
      actions:
        - value: null
  readdir: *hide_not_match
  unlink: &never_allow
    - condition: always
      actions: [{{"allow": False}}]
  write: *never_allow
"""
    with open(f"{ip}_config.yaml", "w") as f:
        f.write(content)
    with open(f"{ip}", "w") as f:
        f.write("unimportant content\n")


if __name__ == '__main__':
    names = "Bletsch", "Hilton", "Board", "Sorin"
    for name in names:
        n_times = 10
        if name == "Bletsch":
            n_times = 9
        for _ in range(n_times):
            ip = make_ip()
            make_yaml(ip, name)
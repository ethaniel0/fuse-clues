## How to run:

### 1. Create a virtual environment and install packages

Please name your virtual environment `venv`. It's recommended to create one like so:

```bash
python -m venv venv
. ./venv/bin/activate
```

Once you've sourced into the virtual environment, install the packagages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Populate the ref folder

The "ref" folder is the folder that FUSE-CLUES will reference all the filesystem operations from before and after displaying everything in the mountpoint folder. So, to have files appear on launch in the mountpoint folder, you must populate the "ref" folder beforehand.

If you want to pull any FUSE tricks, make sure to include a `<filename>_config.yaml` or `<dirname>_config.yaml` file as well.

Here's an example to get you started:

*ref/file.txt*
```
Some normal content here
```
*ref/file.txt_config.yaml*
```yaml
hooks:
  read:
    - condition:
        offset:
          threshold: 10
          mode: gte
      actions:
        - content_text: "Some other text\n"
```

### 3. Run it
```bash
python loopback_fuse.py <ref_folder> <mountpoint>
```
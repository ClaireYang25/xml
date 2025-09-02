# Device Feature Analysis Tool

This repository contains a Python script to parse **XML files from network devices** (currently supported: **ALFO80HDX, AGS20, AGS20M**) and extract feature statistics such as:

* **HQoS** (Hierarchical Quality of Service)
* **QAM profiles** (1024/2048/4096 QAM)
* **Dual Carrier detection**
* **MBL (Multi-Band Link)**
* **Channel bandwidth (e.g. 112 MHz)**

The results are exported into **Excel files** (per-device detail and a summary table).

---

## Features

* Parses XML configurations using [`lxml`](https://lxml.de/).
* Extracts key performance and feature indicators per device.
* Saves results as:

  * 📑 Per-device **detailed Excel** files
  * 📊 Consolidated **summary Excel** with formatted tables
* Extensible design: analyzers per device type are modular.

---

## Requirements

Install dependencies via `pip`:

```bash
pip install pandas lxml xlsxwriter
```

Python 3.8+ is recommended.

---

## Usage

1. Place your XML input files in the `Input` directory (update the `xml_dir` variable in the script accordingly).
   Example expected filenames:

   * `80HDX.xml` → ALFO80HDX
   * `AGS20.xml` → AGS20
   * `AGS20M.xml` → AGS20M

2. Run the script:

```bash
python device_feature_analysis.py
```

3. Outputs:

   * `Device feature statistics details - <DEVICE>.xlsx` → Detailed per-device statistics
   * `Equipment feature statistics summary table.xlsx` → Summary table across all devices

---

## Project Structure

```
.
├── device_feature_analysis.py   # Main script
├── Input - NOV2024/             # Directory for input XML files
├── Device feature statistics details - <DEVICE>.xlsx
├── Equipment feature statistics summary table.xlsx
└── README.md
```

---

## Example Output (Summary)

| Device    | NE Count | HQoS | 1024/2048 QAM | 4096 QAM | Dual Carrier | MBL | 112MHz |
| --------- | -------- | ---- | ------------- | -------- | ------------ | --- | ------ |
| AGS20M    | 12       | 8    | 10            | 3        | 5            | 4   | 6      |
| ALFO80HDX | 5        | 2    | -             | -        | -            | -   | -      |
| AGS20     | 7        | 3    | 5             | -        | -            | -   | -      |

---

## Extending the Tool

* To add support for a new device type:

  1. Define a new `analyze_<device>()` function.
  2. Add the device filename and analyzer mapping in `main()`.

---

## License

This project is released under the MIT License.

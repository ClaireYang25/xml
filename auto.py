
"""
Device Feature Analysis Tool

This script parses XML files from network devices (ALFO80HDX, AGS20, AGS20M),
extracts feature statistics (HQoS, QAM, Dual Carrier, etc.), 
and exports results into Excel files (detailed + summary).

Libraries:
  - os: file handling
  - pandas: tabular data analysis, Excel I/O
  - lxml.etree: XML parsing
  - typing: type annotations
  - xlsxwriter (via pandas): Excel formatting
"""

import os 
import pandas as pd
from lxml import etree
from typing import Dict, List, Any, Callable

# Change this to your directory. For Windows paths, it is recommended to use \r\ or forward slashes.
xml_dir = r'C:/Users/ADMYANGDA/Desktop/XMLautomate/Input - NOV2024'


def parse_xml_root(file_path: str):
    """Parse an XML file and return its root element.

    Args:
        file_path: Absolute path to the XML file.

    Returns:
        Parsed lxml root element.

    Raises:
        Exception: Propagates parsing errors to caller for logging/handling.
    """
    tree = etree.parse(file_path)
    return tree.getroot()


def count_upper_profile_matches(ne_element, substrings: List[str]) -> int:
    """Count UpperProfile nodes whose text contains any of the given substrings."""
    count = 0
    for upper_profile in ne_element.findall('.//UpperProfile'):
        text = upper_profile.text or ''
        if any(sub in text for sub in substrings):
            count += 1
    return count


def count_qos_hqos_matches(ne_element, require_desc_any: List[str]) -> int:
    """Count QOS_PortSchemaSettings nodes matching HQoS oper and a desc containing any token.

    HQoS oper string is matched exactly as used across devices: 'HQoS (4 sch. X 8 queues)'.
    """
    count = 0
    for qos in ne_element.findall('.//QOS_PortSchemaSettings'):
        desc = (qos.findtext('QOS_PortSchemaDesc') or '').strip()
        oper = (qos.findtext('QOS_PortSchemaOper') or '').strip()
        if oper == 'HQoS (4 sch. X 8 queues)' and any(token in desc for token in require_desc_any):
            count += 1
    return count


def count_text_nodes_startswith(ne_element, xpath: str, prefix: str) -> int:
    """Count nodes found by xpath whose text starts with the given prefix."""
    count = 0
    for node in ne_element.findall(xpath):
        text = node.text or ''
        if text.startswith(prefix):
            count += 1
    return count


def count_nodes_with_text_contains(ne_element, xpath: str, substring: str) -> int:
    """Count nodes found by xpath whose text contains the given substring."""
    count = 0
    for node in ne_element.findall(xpath):
        text = node.text or ''
        if substring in text:
            count += 1
    return count


def analyze_alfo80hdx(root) -> List[Dict[str, Any]]:
    """Analyze features for ALFO80HDX devices.

    For this NE type we currently compute only HQoS counts under TRX ports.
    """
    rows: List[Dict[str, Any]] = []
    for ne in root.findall('.//ALFO80HDX'):
        ne_id = (ne.findtext('NEId', default='Unknown') or 'Unknown').strip()
        phys_addr = (
            (ne.findtext('PhysicalAddress') or '')
            or (ne.findtext('.//PhysicalAddress') or '')
            or (ne.findtext('MACAddress') or '')
            or (ne.findtext('.//MACAddress') or '')
        ).strip()

        # HQoS present on TRX ports
        hqos_count = 0
        qos_parent = ne.find('QOS')
        if qos_parent is not None:
            for qos in qos_parent.findall('QOS_PortSchemaSettings'):
                desc = (qos.findtext('QOS_PortSchemaDesc') or '').strip()
                oper = (qos.findtext('QOS_PortSchemaOper') or '').strip()
                if 'TRX' in desc and 'HQoS (4 sch. X 8 queues)' in oper:
                    hqos_count += 1

        rows.append({
            'Typ.Device': 'ALFO80HDX',
            'Physical Address': phys_addr,
            'NE ID': ne_id,
            'HQOS': hqos_count
        })
    return rows


def analyze_ags20m(root) -> List[Dict[str, Any]]:
    """Analyze features for AGS20M devices.

    Features computed:
      - HQoS on RLAG/ODU
      - 1024/2048 QAM
      - 4096 QAM
      - Dual Carrier (OduPartNumber starting with 'GF')
      - MBL (RadioAggregationMemberPort containing 'ALFO')
      - 112MHz (BandAndMod starting with '112')
    """
    rows: List[Dict[str, Any]] = []
    for ne in root.findall('.//AGS-20-M'):
        ne_id = (ne.findtext('NEId', default='Unknown') or 'Unknown').strip()
        phys_addr = (
            (ne.findtext('PhysicalAddress') or '')
            or (ne.findtext('.//PhysicalAddress') or '')
            or (ne.findtext('MACAddress') or '')
            or (ne.findtext('.//MACAddress') or '')
        ).strip()
        feature_count: Dict[str, int] = {}

        feature_count['HQoS'] = count_qos_hqos_matches(ne, ['RLAG', 'ODU'])
        feature_count['1024QAM/2048QAM'] = count_upper_profile_matches(ne, ['1024', '2048'])
        feature_count['4096QAM'] = count_upper_profile_matches(ne, ['4096'])
        feature_count['Dual Carrier'] = count_text_nodes_startswith(ne, './/OduPartNumber', 'GF')
        feature_count['MBL'] = count_nodes_with_text_contains(ne, './/RadioAggregationMemberPort', 'ALFO')
        feature_count['112MHz'] = count_text_nodes_startswith(ne, './/BandAndMod', '112')

        rows.append({
            'Typ.Device': 'AGS20M',
            'Physical Address': phys_addr,
            'NE ID': ne_id,
            **feature_count
        })
    return rows


def analyze_ags20(root) -> List[Dict[str, Any]]:
    """Analyze features for AGS20 devices.

    Features computed:
      - HQoS on ODU
      - 1024/2048 QAM
    """
    rows: List[Dict[str, Any]] = []
    for ne in root.findall('.//AGS20'):
        ne_id = (ne.findtext('NEId', default='Unknown') or 'Unknown').strip()
        phys_addr = (
            (ne.findtext('PhysicalAddress') or '')
            or (ne.findtext('.//PhysicalAddress') or '')
            or (ne.findtext('MACAddress') or '')
            or (ne.findtext('.//MACAddress') or '')
        ).strip()
        feature_count: Dict[str, int] = {}

        # HQoS on ODU
        hqos_count = 0
        for qos in ne.findall('.//QOS_PortSchemaSettings'):
            desc = (qos.findtext('QOS_PortSchemaDesc') or '').strip()
            oper = (qos.findtext('QOS_PortSchemaOper') or '').strip()
            if 'HQoS (4 sch. X 8 queues)' in oper and 'ODU' in desc:
                hqos_count += 1
        feature_count['HQoS'] = hqos_count

        # 1024/2048 QAM
        feature_count['1024QAM/2048QAM'] = count_upper_profile_matches(ne, ['1024', '2048'])

        rows.append({
            'Typ.Device': 'AGS20',
            'Physical Address': phys_addr,
            'NE ID': ne_id,
            **feature_count
        })
    return rows


def summarize_and_export_detail(result_rows: List[Dict[str, Any]]):
    """Export the detailed results and the aggregated summary Excel files."""
    if not result_rows:
        print('No valid data found, no Excel export')
        return

    # Detailed table kept in memory only; no combined details file on disk
    df = pd.DataFrame(result_rows)
    # Reorder to make Physical Address the first column when present
    if 'Physical Address' in df.columns:
        ordered_cols = ['Physical Address'] + [c for c in df.columns if c != 'Physical Address']
        df = df[ordered_cols]

    # Split detailed table per device
    if not df.empty and 'Typ.Device' in df.columns:
        for device_name, sub in df.groupby('Typ.Device'):
            # keep same column order as combined details
            if 'Physical Address' in sub.columns:
                sub = sub[df.columns]
            safe_name = str(device_name).replace('/', '_').replace('\\', '_')
            file_name = f'Device feature statistics details - {safe_name}.xlsx'
            try:
                sub.to_excel(file_name, index=False)
            except PermissionError:
                from datetime import datetime
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                sub.to_excel(f'Device feature statistics details - {safe_name}_{ts}.xlsx', index=False)
        print('Exported per-device detail files alongside the combined details file.')

    # Summary table grouped by device type (use in-memory df)
    device_types = df['Typ.Device'].unique()
    summary_blocks: List[List[List[Any]]] = []

    for device in device_types:
        sub = df[df['Typ.Device'] == device]
        ne_count = sub['NE ID'].nunique()
        block: List[List[Any]] = [[device, ne_count]]
        feature_cols = [col for col in sub.columns if col not in ['Typ.Device', 'NE ID', 'Physical Address']]
        for feat in feature_cols:
            block.append([feat, int(sub[feat].sum())])
        summary_blocks.append(block)

    # Pretty side-by-side tables in a single sheet
    writer = pd.ExcelWriter('Equipment feature statistics summary table.xlsx', engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet('Summary')
    writer.sheets['Summary'] = worksheet

    # Formats
    text_left = workbook.add_format({'border': 1, 'align': 'left'})
    num_right = workbook.add_format({'border': 1, 'align': 'right'})

    header_color_by_device: Dict[str, str] = {
        'ALFO80HDX': '#F4B183',
        'AGS20': '#BDD7EE',
        'AGS20M': '#C6E0B4',
    }

    # Layout
    start_row = 0
    start_col = 0
    col_gap = 2
    worksheet.set_column(0, 100, 20)

    for block in summary_blocks:
        device_name = str(block[0][0])
        header_color = header_color_by_device.get(device_name, '#D9D9D9')
        header_left = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': header_color, 'border': 1})
        header_right = workbook.add_format({'bold': True, 'align': 'right', 'bg_color': header_color, 'border': 1})

        # Header row
        worksheet.write(start_row, start_col + 0, block[0][0], header_left)
        worksheet.write(start_row, start_col + 1, block[0][1], header_right)

        # Feature rows
        r = start_row + 1
        for feature_name, feature_value in block[1:]:
            worksheet.write(r, start_col + 0, feature_name, text_left)
            worksheet.write(r, start_col + 1, feature_value, num_right)
            r += 1

        # Move to next block position
        start_col = start_col + 2 + col_gap

    writer.close()
    print('Exported summary statistics table: Equipment feature statistics summary table.xlsx')


def main():
    """Entry point: iterate XML files, dispatch analyzer by device type, and export results."""
    result: List[Dict[str, Any]] = []

    filename_to_device_type: Dict[str, str] = {
        '80HDX.xml': 'ALFO80HDX',
        'AGS20.xml': 'AGS20',
        'AGS20M.xml': 'AGS20M'
    }

    analyzer_by_device: Dict[str, Callable[[Any], List[Dict[str, Any]]]] = {
        'ALFO80HDX': analyze_alfo80hdx,
        'AGS20M': analyze_ags20m,
        'AGS20': analyze_ags20,
    }

    # Iterate all XML files in the folder and process only known device files
    for filename in os.listdir(xml_dir):
        if not filename.endswith('.xml'):
            continue

        device_type = filename_to_device_type.get(filename)
        if device_type is None:
            continue

        file_path = os.path.join(xml_dir, filename)
        try:
            root = parse_xml_root(file_path)
        except Exception as e:
            print(f"Parsing files {filename} failed: {e}")
            continue

        analyzer = analyzer_by_device.get(device_type)
        if analyzer is None:
            continue

        # Accumulate analysis rows for this file/device type
        result.extend(analyzer(root))

    # Export outputs
    summarize_and_export_detail(result)


if __name__ == '__main__':
    # Kick off execution when running this script directly
    main()


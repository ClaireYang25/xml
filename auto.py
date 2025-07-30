
import os 
import pandas as pd
from lxml import etree
from collections import defaultdict

# 这里改成你的目录，Windows路径推荐用 r'' 或正斜杠 /
xml_dir = r'C:/Users/ADMYANGDA/Desktop/XMLautomate/Input - MAY2025'
result = []

filename_to_device_type = {
    '80HDX.xml': 'ALFO80HDX',
    'AGS20.xml': 'AGS20',
    'AGS20M.xml': 'AGS20M'
}

for filename in os.listdir(xml_dir):
    if not filename.endswith('.xml'):
        continue

    device_type = filename_to_device_type.get(filename)
    if device_type is None:
        continue

    file_path = os.path.join(xml_dir, filename)
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"解析文件 {filename} 失败: {e}")
        continue

    if device_type == 'ALFO80HDX':
        for ne in root.findall('.//ALFO80HDX'):
            ne_id = ne.findtext('NEId', default='Unknown').strip()
            hqos_count = 0
            qos_parent = ne.find('QOS')
            if qos_parent is not None:
                for qos in qos_parent.findall('QOS_PortSchemaSettings'):
                    desc = (qos.findtext('QOS_PortSchemaDesc') or '').strip()
                    oper = (qos.findtext('QOS_PortSchemaOper') or '').strip()
                    if 'TRX' in desc and 'HQoS (4 sch. X 8 queues)' in oper:
                        hqos_count += 1
            result.append({
                '设备类型': device_type,
                'NE ID': ne_id,
                'HQOS': hqos_count
            })

    elif device_type == 'AGS20M':
        for ne in root.findall('.//AGS-20-M'):
            ne_id = ne.findtext('NEId', default='Unknown').strip()
            feature_count = {}

            # HQoS
            count = 0
            for qos in ne.findall('.//QOS_PortSchema'):
                desc = qos.findtext('QOS_PortSchemaDesc', default='')
                oper = qos.findtext('QOS_PortSchemaOper', default='')
                if 'ODU' in desc and 'HQoS (4 sch. X 8 queues)' in oper:
                    count += 1
            feature_count['HQoS'] = count

            # 1024QAM / 2048QAM
            count = 0
            for up in ne.findall('.//UpperProfile'):
                if up.text and ('1024' in up.text or '2048' in up.text):
                    count += 1
            feature_count['1024QAM/2048QAM'] = count

            # 4096QAM
            count = 0
            for up in ne.findall('.//UpperProfile'):
                if up.text and '4096' in up.text:
                    count += 1
            feature_count['4096QAM'] = count

            # Dual Carrier
            count = 0
            for odu in ne.findall('.//OduPartNumber'):
                if odu.text and odu.text.startswith('GF'):
                    count += 1
            feature_count['Dual Carrier'] = count

            # MBL
            count = 0
            for port in ne.findall('.//RadioAggregationMemberPort'):
                if port.text and 'ALFO' in port.text:
                    count += 1
            feature_count['MBL'] = count

            # 112MHz
            count = 0
            for band in ne.findall('.//BandAndMod'):
                if band.text and band.text.startswith('112'):
                    count += 1
            feature_count['112MHz'] = count

            result.append({
                '设备类型': device_type,
                'NE ID': ne_id,
                **feature_count
            })

    elif device_type == 'AGS20':
        for ne in root.findall('.//AGS20'):
            ne_id = ne.findtext('NEId', default='Unknown').strip()
            feature_count = {}

            # HQoS
            hqos_count = 0
            for qos in ne.findall('.//QOS_PortSchemaSettings'):
                desc = qos.findtext('QOS_PortSchemaDesc', '').strip().lower()
                oper = qos.findtext('QOS_PortSchemaOper', '').strip().lower()
                if 'hqoS'.lower() in oper and 'odu' in desc:
                   hqos_count += 1

            feature_count['HQoS'] = hqos_count

            # 1024QAM / 2048QAM
            count = 0
            for up in ne.findall('.//UpperProfile'):
                if up.text and ('1024' in up.text or '2048' in up.text):
                    count += 1
            feature_count['1024QAM/2048QAM'] = count

            result.append({
                '设备类型': device_type,
                'NE ID': ne_id,
                **feature_count
            })

if result:
    df = pd.DataFrame(result)
    df.to_excel('设备feature统计明细.xlsx', index=False)
    print('统计完成，已导出明细表：设备feature统计明细.xlsx')
else:
    print('未找到有效数据，未导出Excel')

if result:
    df = pd.read_excel('设备feature统计明细.xlsx')
    device_types = df['设备类型'].unique()
    summary_blocks = []
    for device in device_types:
        sub = df[df['设备类型'] == device]
        ne_count = sub['NE ID'].nunique()
        block = [[device, ne_count]]
        feature_cols = [col for col in sub.columns if col not in ['设备类型', 'NE ID']]
        for feat in feature_cols:
            block.append([feat, sub[feat].sum()])
        summary_blocks.append(block)

    summary_rows = []
    for block in summary_blocks:
        summary_rows.extend(block)
        summary_rows.append(['', ''])  # 空行分隔
    summary_df = pd.DataFrame(summary_rows, columns=['', ''])
    summary_df.to_excel('设备feature统计总表.xlsx', index=False, header=False)
    print('已导出汇总统计表：设备feature统计总表.xlsx')

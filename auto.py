import os
import pandas as pd
from lxml import etree
from collections import defaultdict

xml_dir = '/Users/claireyang/Desktop/xml/Inputs/Input - MAY2025'
result = []

# 文件名到设备类型的映射
filename_to_device_type = {
    '80HDX.xml': 'ALFO80HDX',
    'AGS20.xml': 'AGS20',
    'AGS20M.xml': 'AGS20M'
}

feature_result = defaultdict(lambda: {'HQOS': 0})

for filename in os.listdir(xml_dir):
    if filename.endswith('.xml'):
        device_type = filename_to_device_type.get(filename)
        if device_type is None:
            continue
        file_path = os.path.join(xml_dir, filename)
        try:
            tree = etree.parse(file_path)
        except Exception as e:
            print(f"解析文件 {filename} 失败: {e}")
            continue
        root = tree.getroot()

        if device_type == 'ALFO80HDX':
            for ne in root.findall('.//ALFO80HDX'):
                ne_id_elem = ne.find('NEId')
                if ne_id_elem is None or not ne_id_elem.text:
                    continue
                ne_id = ne_id_elem.text.strip()
                count = 0
                qos_parent = ne.find('QOS')
                if qos_parent is not None:
                    for qos in qos_parent.findall('QOS_PortSchemaSettings'):
                        desc = (qos.findtext('QOS_PortSchemaDesc') or '').strip()
                        oper = (qos.findtext('QOS_PortSchemaOper') or '').strip()
                        if 'TRX' in desc and 'HQOS' in oper:
                            count += 1
                result.append({
                    '设备类型': device_type,
                    'NE ID': ne_id,
                    'HQOS': count
                })
        elif device_type == 'AGS20M':
            # HQoS
            count = 0
            for qos in ne.findall('.//QOS_PortSchema'):
                desc = qos.findtext('QOS_PortSchemaDesc', default='')
                oper = qos.findtext('QOS_PortSchemaOper', default='')
                if 'HQoS' in oper and ('RLAG' in desc or 'ODU' in desc):
                    count += 1
            feature_count['HQoS'] = count

            # 1024QAM / 2048QAM
            count_1024_2048 = 0
            for up in ne.findall('.//UpperProfile'):
                if up.text and ('1024' in up.text or '2048' in up.text):
                    count_1024_2048 += 1
            feature_count['1024QAM/2048QAM'] = count_1024_2048

            # 4096QAM
            count_4096 = 0
            for up in ne.findall('.//UpperProfile'):
                if up.text and '4096' in up.text:
                    count_4096 += 1
            feature_count['4096QAM'] = count_4096

            # Dual Carrier
            count_dual = 0
            for odu in ne.findall('.//OduPartNumber'):
                if odu.text and odu.text.startswith('GF'):
                    count_dual += 1
            feature_count['Dual Carrier'] = count_dual

            # MBL
            count_mbl = 0
            for port in ne.findall('.//RadioAggregationMemberPort'):
                if port.text and 'ALFO' in port.text:
                    count_mbl += 1
            feature_count['MBL'] = count_mbl

            # 112MHz
            count_112 = 0
            for band in ne.findall('.//BandAndMod'):
                if band.text and band.text.startswith('112'):
                    count_112 += 1
            feature_count['112MHz'] = count_112

        elif device_type == 'AGS20':
            # HQoS
            count = 0
            for qos in ne.findall('.//QOS_PortSchema'):
                desc = qos.findtext('QOS_PortSchemaDesc', default='')
                oper = qos.findtext('QOS_PortSchemaOper', default='')
                if 'HQoS' in oper and 'ODU' in desc:
                    count += 1
            feature_count['HQoS'] = count

            # 1024QAM / 2048QAM
            count_1024_2048 = 0
            for up in ne.findall('.//UpperProfile'):
                if up.text and ('1024' in up.text or '2048' in up.text):
                    count_1024_2048 += 1
            feature_count['1024QAM/2048QAM'] = count_1024_2048

        # 记录结果
        result.append({
            '设备类型': device_type,
            'NE ID': ne_id,
            **feature_count
        })

# 导出明细
if result:
    df = pd.DataFrame(result)
    df.to_excel('设备feature统计明细.xlsx', index=False)
    print('统计完成，已导出Excel')
else:
    print('未找到feature统计明细，未导出Excel')

# 汇总分块统计表
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
        summary_rows.append(['', ''])
    summary_df = pd.DataFrame(summary_rows, columns=['', ''])
    summary_df.to_excel('设备feature统计总表.xlsx', index=False, header=False)
    print('已导出分块统计总表：设备feature统计总表.xlsx')

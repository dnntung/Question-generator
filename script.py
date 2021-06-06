#!/usr/bin/env python
# coding: utf-8

# In[2]:


from torch import log
from underthesea import word_tokenize
from underthesea import pos_tag
from underthesea import sent_tokenize
from underthesea import dependency_parse
from underthesea import ner
from underthesea import classify
from underthesea import chunk

import random
import sys
import os

# In[3]:


import re
# Bỏ khoảng trắng trước PUNCT
def removeSpaceFrontPunct(s):
    s = re.sub(r'\s([?.!"](?:\s|$))', r'\1', s)
    s = s.replace(' ,', ',')
    return s


# In[103]:


def dp_tree(s):
    s_ner = ner(s)
    s_dp = dependency_parse(s)
    s_dp_tree = []
    for i in range(len(s_dp)):
        tmp = []
        for j in range(6):
            if j < 3:
                if j == 1:
                    tmp.append(s_dp[i][j]-1)
                else:
                    tmp.append(s_dp[i][j])
            else:
                tmp.append(s_ner[i][j-2])
        s_dp_tree.append(tmp)
    
    # Tìm các nhánh con
    for i in range(len(s_dp_tree)):
        tmp_tree = []
        for j in range(len(s_dp_tree)):
            if i == j:
                tmp_tree.append(j)
            if s_dp[j][1]-1 == i:
                tmp_tree.append(j)
        s_dp_tree[i].append(tmp_tree)
    
    # Chuyển thành tuple
    for i in range(len(s_dp_tree)):
        s_dp_tree[i] = tuple(s_dp_tree[i])
    
    return s_dp_tree

# Kiểm tra trong Tiếng Việt có trường hợp nào đặc biệt (có nút a và bé hơn cha nó, kiểm tra xem con lớn của nút a có lớn hơn cha của a không)
def duyet_cay(s_dp_tree, index):
    # Tìm các index con
    childs_index = s_dp_tree[index][-1]
    if len(childs_index) == 1:
        return str(index)
    
    cum = ''
    for i in childs_index:
        if i != index:
            cum += ' ' + duyet_cay(s_dp_tree, i)
        else:
            cum += ' ' + str(index)
    
    # Xoá các khoảng trắng dư thừa
    cum = " ".join(cum.split())
    return cum

def check_special_case(s_dp_tree, index):
    os = duyet_cay(s_dp_tree, index)
    os = os.split()
    for i in range(len(os)):
        os[i] = int(os[i])
    for i in range(len(os)-1):
        for j in range(i+1, len(os)):
            # Special case
            if i > j:
                return True
            
    for i in range(len(os)-1):
        if os[i+1]-os[i] > 1:
            return True
    return False

# Xác định cụm từ bằng đệ quy và DP-Tree
def xd_ct(s_dp_tree, index):
    if check_special_case(s_dp_tree, index):
        return "TRƯỜNG HỢP ĐẶC BIỆT"
    
    order_cum = duyet_cay(s_dp_tree, index)
    order_cum = order_cum.split()
    cum = ''
    for i in order_cum:
        index = int(i)
        cum += ' ' + s_dp_tree[index][0]
        
    cum = cum.strip()
    # Xoá khoảng trắng trước dấu
    cum = removeSpaceFrontPunct(cum)
    cum = cum.replace("' ", "'", 1)
    cum = cum.replace(" ' ", "' ", 1)
    return cum

con = 'con trai, con gái, con nuôi, con tàu, con thuyền, con sông, con nước, con kênh, con ngươi, con mắt'
def xd_nguoi_vat(subj):
    set_daitu = daitu.split(', ')
    set_con = con.split(', ')
    for i in subj.split(' '):
        if i.lower() in set_daitu:
            return 0
    for i in subj.split(' '):
        if i.lower() == 'con':
            for j in set_con:
                if j in subj.lower():
                    if j == 'con trai' or j == 'con gái' or j == 'con nuôi':
                        return 0
                    else:
                        return 2
            return 1
    return 2

def vhccd(s):
    s = s.strip()
    return s[0].upper() + s[1:]

def xvhccd(s):
    s = s.strip()
    return s[0].lower() + s[1:]

def xdccc(s):
    s = s.strip()
    if s[-3:] == '...':
        s = s[:-3]
    if s[-1] == '.':
        s = s[:-1]
    return s


# In[6]:

dongtu_ymuon = 'toan, định, dám, chịu, buồn, nỡ, dự định, muốn, mong, chúc'
dongtu_batdau_tiepdien_ketthuc = 'bắt đầu, tiếp tục, hết, thôi, chuẩn bị'
daitu = 'tôi, tao, ta, tớ, mình, chúng tôi, chúng ta, chúng tớ, chúng tao, chúng mình, bọn tao, bạn, các bạn, đằng ấy, mày, bọn mày, tên kia, anh, cậu, ông, gã, y, hắn, thằng, cô, chị, bà, ả, thị, cổ, bả, chúng nó, họ, bọn họ, bọn chúng, nó, bác, chú, mợ, dì, thím, nhân, dân, chủ, người, thầy, công, vợ, chồng, mẹ, cha, ba, tía, má, u, bầm, nữ, bố, trai, gái'
gioitu_noichon = 'ở, tại, trong, ngoài, trên, dưới, giữa'
gioitu_cachthuc = 'bằng'
gioitu_thoigian = 'vào, lúc, khi'

def bongu_mieuta(s, s_dp):
    ns = s
    if s[-1] == '.':
        ns = s[:-1]
    #s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            root_index = i
            break
    
    # Đặt câu hỏi cho bổ ngữ miêu tả (trả lời cho câu hỏi cách thức, trạng thái, tính chất, mục đích, nơi chốn)
    qa = []
    list_obl = []
    for i in s_dp[root_index][6]:
        if i <= root_index:
            continue
        if 'obl' in s_dp[i][2] and s_dp[i][1] == root_index:
            list_obl.append(i)
            cum_tn = xd_ct(s_dp, i)
            list_gt = []
            for j in s_dp[i][6]:
                if s_dp[j][4] == 'B-PP':
                    list_gt.append(j)
            if len(list_gt) >= 1:
                # Trường hợp có giới từ
                # Giới từ chỉ cách thức
                for i in list_gt:
                    if s_dp[i][0].lower() == 'bằng':
                        qa.append(['Bằng cách nào ' + xvhccd(s[:-1].replace(' ' + cum_tn, '')) + '?', vhccd(cum_tn)])

                # Giới từ chỉ nơi chốn
                set_gioitu_noichon = gioitu_noichon.split(', ')
                for i in list_gt:
                    if s_dp[i][0].lower() in set_gioitu_noichon:
                        qa.append([ns.replace(' ' + cum_tn, '') + ' ở đâu?', vhccd(cum_tn)])
                # Giới từ chỉ thời gian
                set_gioitu_thoigian = gioitu_thoigian.split(', ')
                for i in list_gt:
                    if s_dp[i][0].lower() in set_gioitu_thoigian:
                        qa.append(['Khi nào ' + xvhccd(ns.replace(' ' + cum_tn, '')) + '?', vhccd(cum_tn)])

            else:
                if 'tmod' in s_dp[i][2]:
                    for i in s_dp[i][6]:
                        if s_dp[i][0].lower() == 'ngày':
                            qa.append(['Vào ngày mấy ' + xvhccd(ns.replace(' ' + cum_tn, '')) + '?', vhccd(cum_tn)])
                            return qa
                    qa.append(['Khi nào ' + xvhccd(ns.replace(' ' + cum_tn, '')) + '?', vhccd(cum_tn)])
    return qa
# In[250]:

### TEMPLATE Chủ ngữ + là + danh từ 

### TEMPLATE Chủ ngữ + là + danh từ 
def temp_cn_la_danhtu(s, s_dp):
    #s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            if s_dp[i][4] != 'B-NP':
                return 'SAI FORMAT'
            if root_index is None:
                root_index = i
            else:
                return 'SAI FORMAT'
    if root_index is None:
        return 'SAI FORMAT'
    
    # Check format: Chủ ngữ phải xuất hiện đầu câu, không thành phần phụ
    cn_index = s_dp[root_index][6][0]
    if 'subj' not in s_dp[cn_index][2]:
        return 'SAI FORMAT'
    
    # Check nhiều chủ ngữ
    for i in range(cn_index+1, root_index):
        if 'subj' in s_dp[i][2]:
            return 'SAI FORMAT'
        
    # Check vị trí từ "là"
    la_index = None
    for i in range(s_dp[cn_index][6][-1] + 1, root_index):
        if s_dp[i][2] == 'cop' and s_dp[i][0] == 'là' and len(s_dp[i][6]) == 1:
            if la_index is None:
                la_index = i
            else:
                return 'SAI FORMAT'
            
    if la_index is None:
        for i in range(s_dp[cn_index][6][-1] + 1, root_index):
            if 'NP' not in s_dp[i][4]:
                return 'SAI FORMAT'
        s = s.replace(vhccd(xd_ct(s_dp, cn_index)), vhccd(xd_ct(s_dp, cn_index)) + ' có')
        s_dp = dp_tree(s)
        return temp_cn_dongtu(s, s_dp)
    

   
    # Check format: Danh từ xuất hiện cuối câu, chỉ có danh từ là root.
    for i in range(la_index + 1, len(s_dp)-1):
        mqh = s_dp[i][2]
        if mqh == 'advcl' or mqh == 'parataxis' \
            or mqh == 'mark' or mqh == 'ccomp':
            return 'SAI FORMAT'
        # Nếu có trường hợp conj và cc thì kiểm tra có phải là mệnh đề không (kiểm tra kiểu chunking)
        if mqh == 'conj':
            for j in s_dp[i][6]:
                if s_dp[j][4] != 'B-NP' and s_dp[j][4] != 'B-PP' and s_dp[j][2] != 'cc' and s_dp[j][2] != 'punct':
                    print(s_dp[j][4])
                    return 'SAI FORMAT'
    
    qa = []
    # Trường hợp ccn = 0: Chủ ngữ là trường hợp khác
    ccn = 0
    subj = xd_ct(s_dp, cn_index)
    danhtu = ''
    for i in range(la_index + 1, len(s_dp)-1):
        if s_dp[i][2] == 'punct':
            danhtu += s_dp[i][0]
        else:
            danhtu += ' ' + s_dp[i][0]
    danhtu = danhtu.strip()
    # Trường hợp ccn = 4: Chủ ngữ là cụm tính từ
    if 'asubj' in s_dp[cn_index][2]:
        ccn = 4
        qa.append([subj + ' là gì?', vhccd(xdccc(danhtu))])
        qa.append([vhccd(xdccc(danhtu)) + ' là gì?', subj])
        
    # Trường hợp ccn = 3: Chủ ngữ là cụm động từ
    if 'vsubj' in s_dp[cn_index][2]:
        ccn = 3
        qa.append([subj + ' là gì?', vhccd(xdccc(danhtu))])
        qa.append(['Hành động nào là ' + xdccc(danhtu) + '?', subj])
    
    loc = False
    if 'nsubj' in s_dp[cn_index][2] and s_dp[cn_index][4] == 'B-NP':
        # Trường hợp ccn = 2: Chủ ngữ là cụm danh từ
        ccn = 2
        for i in s_dp[cn_index][6]:
            if 'NP' not in s_dp[i][4]:
                if s_dp[i][2] != 'amod' or s_dp[i][2] != 'case' or s_dp[i][2] != 'compound:vmod' or s_dp[i][2] != 'acl:subj':
                    # Trường hợp ccn = 1: Chủ ngữ là mệnh đề chủ ngữ và vị ngữ --> không đặt câu hỏi chủ ngữ cho trường hợp này
                    ccn = 1
                    break
        
        # ĐẶT CÂU HỎI CHO CHỦ NGỮ
        if ccn == 2:
            for i in s_dp[cn_index][6]:
                # Trường hợp chủ ngữ là tên riêng PER (NER)
                if ('PER' in s_dp[i][5]):
                    qa.append([vhccd(xdccc(danhtu)) + ' có tên là gì?', subj])
                    break
                # Trường hợp chủ ngữ là tên địa danh LOC (NER)
                elif ('LOC' in s_dp[i][5]):
                    qa.append(['Đâu là ' + xdccc(danhtu) + '?', subj])
                    loc = True
                    break
            
            if len(qa) == 0:
                # Trường hợp chủ ngữ là đại từ nhân xưng
                set_daitu = daitu.split(', ')
                for i in subj.split(' '):
                    if i.lower() in set_daitu:
                        qa.append([vhccd(xdccc(danhtu)) + ' là ai?', subj])
                        break
                        
            if len(qa) == 0:
                for i in s_dp[cn_index][6]:
                    # Trường hợp chủ ngữ là con vật
                    if s_dp[i][0].lower() == 'con' and 'clf' in s_dp[i][2] and 'con gái' not in subj.lower() and 'con trai' not in subj.lower():
                        qa.append([vhccd(xdccc(danhtu)) + ' là con gì?', subj])
                        break

            # Trường hợp chủ ngữ là vật
            if len(qa) == 0:
                qa.append([vhccd(xdccc(danhtu)) + ' là gì?', subj])
            
            
    # ĐẶT CÂU HỎI CHO VỊ NGỮ
    if len(qa) <= 1:
        generate = True
        
        # Trường hợp vị ngữ là tên riêng PER (NER)
        if (s_dp[root_index][5] == 'B-PER'):
            qa.append([subj + ' có tên là gì?', vhccd(xdccc(danhtu))])
            generate = False
            
        # Trường hợp vị ngữ là tên địa danh LOC (NER)
        if (s_dp[root_index][5] == 'B-LOC') and loc:
            qa.append([subj + ' là đâu?', vhccd(xdccc(danhtu))])
            generate = False
            

        
        if generate:
            # Trường hợp vị ngữ là đại từ nhân xưng
            set_daitu = daitu.split(', ')
            
            for i in s_dp[root_index][0].split(' '):
                if i.lower() in set_daitu:
                    qa.append([subj + ' là ai?', vhccd(xdccc(danhtu))])
                    generate = False
                    break

        if generate:
            for i in s_dp[root_index][6][la_index+1:root_index]:
                # Trường hợp vị ngữ là con vật
                if s_dp[i][0].lower() == 'con' and 'clf' in s_dp[i][2] and 'con gái' not in subj.lower() and 'con trai' not in subj.lower():
                    qa.append([subj + ' là con gì?', vhccd(xdccc(danhtu))])
                    generate = False
                    break

        # Trường hợp vị ngữ là vật
        if generate:
            qa.append([subj + ' là gì?', vhccd(xdccc(danhtu))])
    qa.extend(bongu_mieuta(s, s_dp))
    return qa
    

# In[251]:


### TEMPLATE Chủ ngữ + (là) + tính từ
### TEMPLATE Chủ ngữ + (là) + tính từ
### TEMPLATE Chủ ngữ + (là) + tính từ
def temp_cn_tinhtu(s, s_dp):
    #s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            if s_dp[i][4] != 'B-AP':
                return 'SAI FORMAT'
            if root_index is None:
                root_index = i
            else:
                return 'SAI FORMAT'
    if root_index is None:
        return 'SAI FORMAT'
    
    # Check format: Chủ ngữ phải xuất hiện đầu câu, không thành phần phụ
    cn_index = s_dp[root_index][6][0]
    if 'subj' not in s_dp[cn_index][2]:
        return 'SAI FORMAT'
    
    # Check nhiều chủ ngữ
    for i in range(cn_index+1, root_index):
        if 'subj' in s_dp[i][2]:
            return 'SAI FORMAT'

    # Check format: Tính từ xuất hiện cuối câu, chỉ có tính từ là root.
    last_cn_index = s_dp[cn_index][6][-1]
    for i in range(last_cn_index + 1, len(s_dp)-1):
        mqh = s_dp[i][2]
        if mqh == 'advcl' or mqh == 'parataxis' \
            or mqh == 'mark' or mqh == 'ccomp':
            return 'SAI FORMAT'
        # Nếu có trường hợp conj và cc thì kiểm tra có phải là mệnh đề không (kiểm tra kiểu chunking)
        if mqh == 'conj':
            for j in s_dp[i][6]:
                if s_dp[j][4] != 'B-AP' and s_dp[j][2] != 'cc' and s_dp[j][2] != 'punct':
                    return 'SAI FORMAT'
                
    qa = []
    # Trường hợp ccn = 0: Chủ ngữ là trường hợp khác
    ccn = 0
    subj = xd_ct(s_dp, cn_index)
    tinhtu = s.replace(subj + ' ', '')
    # Bỏ các thành phần phụ sau của tính từ
    for i in s_dp[root_index][6]:
        if i > root_index and s_dp[i][1] == root_index and (s_dp[i][2] == 'advmod' or s_dp[i][3] == 'R'):
            tinhtu = tinhtu.replace(' ' + s_dp[i][0], '')
            
    # Trường hợp ccn = 4: Chủ ngữ là cụm tính từ
    if 'asubj' in s_dp[cn_index][2]:
        ccn = 4
        return []
        
    # Trường hợp ccn = 3: Chủ ngữ là cụm động từ
    if 'vsubj' in s_dp[cn_index][2]:
        ccn = 3
        qa.append([subj + ' có đặc điểm gì?', vhccd(xdccc(tinhtu))])
        qa.append(['Hành động nào có đặc điểm ' + xdccc(tinhtu) + '?', subj])
    
    if 'nsubj' in s_dp[cn_index][2] and s_dp[cn_index][4] == 'B-NP':
        # Trường hợp ccn = 2: Chủ ngữ là cụm danh từ
        ccn = 2
        for i in s_dp[cn_index][6]:
            if 'NP' not in s_dp[i][4]:
                if s_dp[i][2] != 'amod' or s_dp[i][2] != 'case' or s_dp[i][2] != 'compound:vmod' or s_dp[i][2] != 'acl:subj':
                    # Trường hợp ccn = 1: Chủ ngữ là mệnh đề chủ ngữ và vị ngữ --> không đặt câu hỏi chủ ngữ cho trường hợp này
                    ccn = 1
                    break
            
        # ĐẶT CÂU HỎI CHO CHỦ NGỮ
        if ccn == 2:
            # Trường hợp chủ ngữ là tên riêng PER (NER)
            if (s_dp[cn_index][5] == 'B-PER'):
                qa.append(['Ai ' + xdccc(tinhtu) + '?', subj])
                
            # Trường hợp chủ ngữ là tên địa danh LOC (NER)
            elif (s_dp[cn_index][5] == 'B-LOC'):
                qa.append(['Đâu là nơi ' + xdccc(tinhtu) + '?', subj])
                
            
            if len(qa) == 0:
                # Trường hợp chủ ngữ là đại từ nhân xưng
                set_daitu = daitu.split(', ')
                for i in subj.split(' '):
                    if i.lower() in set_daitu:
                        qa.append(['Ai ' + xdccc(tinhtu) + '?', subj])
                        break
                        
            if len(qa) == 0:
                for i in s_dp[cn_index][6]:
                    # Trường hợp chủ ngữ là con vật
                    if s_dp[i][0].lower() == 'con' and 'clf' in s_dp[i][2] and 'con gái' not in subj.lower() and 'con trai' not in subj.lower():
                        qa.append(['Con gì ' + xdccc(tinhtu) + '?', subj])
                        break

            # Trường hợp chủ ngữ là vật
            if len(qa) == 0:
                qa.append(['Cái gì ' + xdccc(tinhtu) + '?', subj])
    # ĐẶT CÂU HỎI CHO VỊ NGỮ
    if len(qa) <= 1:
        qa.append([subj + ' có đặc điểm gì?', vhccd(xdccc(tinhtu))])
    qa.extend(bongu_mieuta(s, s_dp))
    return qa

# In[301]:


### TEMPLATE Chủ ngữ + động từ
### TEMPLATE Chủ ngữ + động từ
def temp_cn_dongtu(s, s_dp):
    #s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            if s_dp[i][4] != 'B-VP':
                return 'SAI FORMAT'
            if root_index is None:
                root_index = i
            else:
                return 'SAI FORMAT'
            
    if root_index is None:
        return 'SAI FORMAT'
    
    # Check format: Chủ ngữ phải xuất hiện đầu câu, không thành phần phụ
    cn_index = s_dp[root_index][6][0]
    if 'subj' not in s_dp[cn_index][2]:
        return 'SAI FORMAT'
    
    # Check nhiều chủ ngữ
    for i in range(cn_index+1, root_index):
        if 'subj' in s_dp[i][2]:
            return 'SAI FORMAT'

    # Check format: Động từ xuất hiện cuối câu, chỉ có động từ là root.
    last_cn_index = s_dp[cn_index][6][-1]
    for i in range(last_cn_index + 1, len(s_dp)-1):
        mqh = s_dp[i][2]
        if mqh == 'advcl' or mqh == 'parataxis' or mqh == 'mark':
            return 'SAI FORMAT'
        # Nếu có trường hợp conj và cc thì kiểm tra có phải là mệnh đề không (kiểm tra kiểu chunking)
        if mqh == 'conj':
            for j in s_dp[i][6]:
                if s_dp[j][4] != 'B-VP' and s_dp[j][2] != 'cc' and s_dp[j][2] != 'punct':
                    return 'SAI FORMAT'
    
    # Loại bỏ tất cả trường hợp phủ định
    for i in range(last_cn_index + 1, root_index):
        if 'neg' in s_dp[i][2]:
            return 'SAI FORMAT'
    
    # Lấy thành phần phụ đầu của vị ngữ
    phutruoc_dongtu = ''
    for i in range(last_cn_index + 1, root_index):
        phutruoc_dongtu += s_dp[i][0] + ' '
    phutruoc_dongtu = phutruoc_dongtu.strip()
    
    qa = []
    vn_dongtu = 0
    subj = xd_ct(s_dp, cn_index)
    dongtu = s.replace(subj + ' ', '')
    set_dongtu_ymuon = dongtu_ymuon.split(', ')
    set_dongtu_batdau_tiepdien_ketthuc = dongtu_batdau_tiepdien_ketthuc.split(', ')
    
    
    # ĐẶT CÂU HỎI CHO CHỦ NGỮ
    if 'nsubj' in s_dp[cn_index][2] and s_dp[cn_index][4] == 'B-NP':
        # Trường hợp ccn = 2: Chủ ngữ là cụm danh từ
        ccn = 2
        for i in s_dp[cn_index][6]:
            if 'NP' not in s_dp[i][4]:
                if s_dp[i][2] != 'amod' or s_dp[i][2] != 'case' or s_dp[i][2] != 'compound:vmod' or s_dp[i][2] != 'acl:subj':
                    # Trường hợp ccn = 1: Chủ ngữ là mệnh đề chủ ngữ và vị ngữ --> không đặt câu hỏi chủ ngữ cho trường hợp này
                    ccn = 1
                    break

        # ĐẶT CÂU HỎI CHO CHỦ NGỮ
        if ccn == 2:
            
            # Trường hợp chủ ngữ là tên riêng PER (NER)
            if (s_dp[cn_index][5] == 'B-PER'):
                qa.append(['Ai ' + xdccc(dongtu) + '?', subj])
                
            # Trường hợp chủ ngữ là tên địa danh LOC (NER)
            elif (s_dp[cn_index][5] == 'B-LOC'):
                qa.append(['Đâu là nơi ' + xdccc(dongtu) + '?', subj])
                

            if len(qa) == 0:
                # Trường hợp chủ ngữ là đại từ nhân xưng
                set_daitu = daitu.split(', ')
                for i in subj.split(' '):
                    if i.lower() in set_daitu:
                        qa.append(['Ai ' + xdccc(dongtu) + '?', subj])
                        break

            if len(qa) == 0:
                for i in s_dp[cn_index][6]:
                    # Trường hợp chủ ngữ là con vật
                    if s_dp[i][0].lower() == 'con' and 'clf' in s_dp[i][2] and 'con gái' not in subj.lower() and 'con trai' not in subj.lower():
                        qa.append(['Con gì ' + xdccc(dongtu) + '?', subj])
                        break

            # Trường hợp chủ ngữ là vật
            if len(qa) == 0:
                qa.append(['Cái gì ' + xdccc(dongtu) + '?', subj])

    
    # Xác định thể bị động
    auxpass_index = None
    for i in range(last_cn_index + 1, root_index):
        if s_dp[i][2] == 'aux:pass':
            if auxpass_index is None:
                auxpass_index = i
            else:
                return 'SAI FORMAT'
    if auxpass_index is not None:
        agent_index = None
        for i in range(auxpass_index + 1, len(s_dp) - 1):
            if s_dp[i][1] == root_index and s_dp[i][2] == 'obl:agent':
                agent_index = i
                break
        
        ans_vn = ''
        for j in range(auxpass_index, len(s_dp) - 1):
            ans_vn += s_dp[j][0] + ' '
        qa.append([vhccd(xd_ct(s_dp, cn_index)) + ' ' + s_dp[auxpass_index][0] + ' gì?', vhccd(ans_vn.strip())])
        if agent_index is not None:
            theloai_agent = xd_nguoi_vat(xd_ct(s_dp, agent_index))
            loai = 'cái gì'
            if theloai_agent == 0:
                loai = 'ai'
            elif theloai_agent == 1:
                loai = 'con gì'
            qa.append([s[:-1].replace(xd_ct(s_dp, agent_index), loai) + '?', vhccd(xd_ct(s_dp, agent_index))])
    else:
        # Xác định template
        for i in range(root_index, len(s_dp)-1):
            mqh = s_dp[i][2]
            cn_index_ccomp = s_dp[i][6][0]
            # Trường hợp vn_dongtu = 11: Root là động từ có.
            if s_dp[root_index][0] == 'có':
                vn_dongtu = 11
                for i in range(root_index+1, len(s_dp)-1):
                    if s_dp[i][2] == 'acomp' and s_dp[i][6][-1] == len(s_dp)-2:
                        qa.append([s[:-1].replace(xd_ct(s_dp, i), 'như thế nào') + '?', vhccd(xd_ct(s_dp, i))])
                after_sent = ''
                for j in range(root_index, len(s_dp)-1):
                    after_sent += s_dp[j][0] + ' '
                qa.append([subj + ' có cái gì?', vhccd(after_sent.strip())])
                break
            
            # Truong hop vn_dongtu = 1: Subj + V(root) + Subj + (V/N/A)(ccomp) + (obj)
            elif s_dp[i][1] == root_index and mqh == 'ccomp' and 'subj' in s_dp[cn_index_ccomp][2]:
                vn_dongtu = 1
                bongu_ccomp = xd_ct(s_dp, i)
                bongu_ccomp_dp = dp_tree(bongu_ccomp)
                pre_sent = s.replace(bongu_ccomp, '')
                pre_sent = pre_sent[:-1].strip()
                cn_dongtu = temp_cn_dongtu(bongu_ccomp, bongu_ccomp_dp)
                cn_tinhtu = temp_cn_tinhtu(bongu_ccomp, bongu_ccomp_dp)
                cn_la_danhtu = temp_cn_la_danhtu(bongu_ccomp, bongu_ccomp_dp)
                if (cn_dongtu != 'SAI FORMAT'):
                    for j in range(len(cn_dongtu)):
                        qa.append([pre_sent + ' ' + xvhccd(cn_dongtu[j][0]), cn_dongtu[j][1]])
                elif (cn_tinhtu != 'SAI FORMAT'):
                    for j in range(len(cn_tinhtu)):
                        qa.append([pre_sent + ' ' + xvhccd(cn_tinhtu[j][0]), cn_tinhtu[j][1]])
                elif (cn_la_danhtu != 'SAI FORMAT'):
                    for j in range(len(cn_la_danhtu)):
                        qa.append([pre_sent + ' ' + xvhccd(cn_la_danhtu[j][0]), cn_la_danhtu[j][1]])


            # Truong hop vn_dongtu = 2: Subj + V(root)(ý muốn) + V(comp/compound) + (obj)
            elif s_dp[i][1] == root_index and 'comp' in mqh and mqh != 'ccomp' and s_dp[i][4] == 'B-VP' and s_dp[root_index][0].lower() in set_dongtu_ymuon:
                vn_dongtu = 2
                #after_sent = ''
                #for j in range(root_index+1, len(s_dp)-1):
                    #after_sent += s_dp[j][0] + ' '
                qa.append([subj + ' ' + phutruoc_dongtu + ' ' + s_dp[root_index][0].lower() + ' làm gì?', vhccd(xd_ct(s_dp, i))])
                break

            # Truong hop vn_dongtu = 3: Subj + V(root)(bắt đầu/kết thúc/tiếp diễn) + (V(comp/compound)/obj) + (obj)
            elif s_dp[root_index][0].lower() in set_dongtu_batdau_tiepdien_ketthuc and ('obj' in mqh or 'comp' in mqh) and s_dp[i][1] == root_index:
                vn_dongtu = 3
                if 'obj' in s_dp[i][2]:
                    qa.append([subj + ' ' + phutruoc_dongtu + ' ' + s_dp[root_index][0].lower() + ' điều gì?', vhccd(xd_ct(s_dp, i))])
                else:
                    qa.append([subj + ' ' + phutruoc_dongtu + ' ' + s_dp[root_index][0].lower() + ' làm gì?', vhccd(xd_ct(s_dp, i))])
                break

            # Trường hợp vn_dongtu = 4: Subj + V(root) + compound:dir + obj
            elif s_dp[i][1] == root_index and 'dir' in mqh and s_dp[i][4] == 'B-VP':
                vn_dongtu = 4
                after_sent = ''
                for j in range(root_index, len(s_dp)-1):
                    after_sent += s_dp[j][0] + ' '
                if s_dp[root_index][0] != 'đi':
                    qa.append([subj + ' ' + phutruoc_dongtu + ' ' + s_dp[root_index][0] + ' đi đâu?', vhccd(after_sent.strip())])
                else:
                    qa.append([subj + ' ' + phutruoc_dongtu + ' ' + s_dp[root_index][0] + ' đâu?', vhccd(after_sent.strip())])
                break

            # Trường hợp vn_dongtu = 5: Subj + V(root)(động từ mang ý nghĩa nối kết) + obj + (cùng/với) + obl:with
            elif s_dp[i][1] == root_index and 'obl:with' in mqh and s_dp[i][4] == 'B-NP':
                vn_dongtu = 5
                obj_index = None
                for j in range(root_index, s_dp[i][6][-1]):
                    if 'obj' in s_dp[j][2]:
                        obj_index = j
                        break
                if obj_index is not None:
                    qa.append([subj + ' ' + phutruoc_dongtu + ' ' + s_dp[root_index][0].lower() + ' ' + xd_ct(s_dp, obj_index) + ' với gì?', vhccd(xd_ct(s_dp, i))])
                break

            # Trường hợp vn_dongtu = 6: Sau root là 'từ'
            elif s_dp[i][1] == root_index and 'obl:' in s_dp[i][2] and 'comp' in s_dp[i][2] :
                vn_dongtu = 6
                if 'LOC' in s_dp[i][5]:
                    qa.append([s[:-1].replace(xd_ct(s_dp, i), 'đâu') + '?', vhccd(xd_ct(s_dp, i))])
                else:
                    qa.append([s[:-1].replace(xd_ct(s_dp, i), 'gì') + '?', vhccd(xd_ct(s_dp, i))])
                break

            
            elif s_dp[i][1] == root_index and mqh == 'obj':
                
                # Trường hợp vn_dongtu = 7: Sau root có obj và có động từ con của động từ. VD: Tôi mua hoa tặng cho mẹ.
                vn_dongtu = 7
                iobj = None
                for j in range(root_index+1, len(s_dp)-1):
                    if 'iobj' in s_dp[j][2]:
                        iobj = j
                if iobj is not None:
                    for j in range(root_index+1, len(s_dp)-1):
                        if 'obj' in s_dp[j][2]:
                            theloai_obj = xd_nguoi_vat(xd_ct(s_dp, j))
                            loai = 'cái gì'
                            if theloai_obj == 0:
                                loai = 'ai'
                            elif theloai_obj == 1:
                                loai = 'con gì'
                            if 'iobj' in s_dp[j][2]:
                                loai = 'cho ' + loai
                            qa.append([s[:-1].replace(xd_ct(s_dp, j), loai) + '?', vhccd(xd_ct(s_dp, j))])
                        
                    if s_dp[iobj][1] != root_index:
                        parent = s_dp[iobj][1]
                        qa.append([s[:-1].replace(xd_ct(s_dp, parent), 'để làm gì') + '?', vhccd(xd_ct(s_dp, parent))])
                        
                else:
                    for j in range(root_index+1, len(s_dp)-1):
                        if s_dp[j][2] == 'obj':
                            theloai_obj = xd_nguoi_vat(xd_ct(s_dp, j))
                            loai = 'cái gì'
                            if theloai_obj == 0:
                                loai = 'ai'
                            elif theloai_obj == 1:
                                loai = 'con gì'
                            parent = s_dp[j][1]
                            
                            if parent == root_index:
                                quesobj = vhccd(xd_ct(s_dp, cn_index)) + ' ' + s_dp[root_index][0] + ' ' + xd_ct(s_dp, j) + '?'
                            else:
                                quesobj = vhccd(xd_ct(s_dp, cn_index)) + ' ' + xd_ct(s_dp, parent) + '?'
                            if s_dp[parent][0].lower() == 'đi' or s_dp[parent][0].lower() == 'về' or s_dp[parent][0].lower() == 'đến' or s_dp[parent][0].lower() == 'tới':
                                qa.append([quesobj.replace(xd_ct(s_dp, j), 'đâu'), vhccd(xd_ct(s_dp, j))])
                            else:
                                qa.append([quesobj.replace(xd_ct(s_dp, j), loai), vhccd(xd_ct(s_dp, j))])

            # Trường hợp vn_dongtu = 10: Sau root là một acomp bổ ngữ cho động từ.
            elif s_dp[i][1] == root_index and 'acomp' in mqh and s_dp[i][4] == 'B-AP':
                vn_dongtu = 10
                qa.append([subj + ' ' + s_dp[root_index][0] + ' như thế nào?', vhccd(xd_ct(s_dp, i))])
                break
            '''
            elif s_dp[i][1] == root_index and 'obj' in mqh:
                # Trường hợp vn_dongtu = 7: Sau root là 2 obj. VD: Tôi biếu thầy cái bánh.
                confirm_break = False
                for j in range(i+1, len(s_dp)-1):
                    if s_dp[j][1] == root_index and 'obj' in s_dp[j][2]:
                        vn_dongtu = 7
                        if 'iobj' in s_dp[i][2]:
                            qa.append([subj + ' ' + s_dp[root_index][0].lower() + ' ' + xd_ct(s_dp, j) + ' cho ai?', vhccd(xd_ct(s_dp, i))])
                            qa.append([subj + ' ' + s_dp[root_index][0].lower() + ' ' + xd_ct(s_dp, i) + ' cái gì?', vhccd(xd_ct(s_dp, j))])
                        elif 'iobj' in s_dp[j][2]:
                            qa.append([subj + ' ' + s_dp[root_index][0].lower() + ' ' + xd_ct(s_dp, i) + ' cho ai?', vhccd(xd_ct(s_dp, j))])
                            qa.append([subj + ' ' + s_dp[root_index][0].lower() + ' ' + xd_ct(s_dp, j) + ' cái gì?', vhccd(xd_ct(s_dp, i))])
                        elif s_dp[i][3] == 'Np' and s_dp[i][3] != 'Np':
                            qa.append([subj + ' ' + s_dp[root_index][0].lower() + ' ' + xd_ct(s_dp, j) + ' cho ai?', vhccd(xd_ct(s_dp, i))])
                            qa.append([subj + ' ' + s_dp[root_index][0].lower() + ' cho ' + xd_ct(s_dp, i) + ' cái gì?', vhccd(xd_ct(s_dp, j))])
                        else:
                            qa.append([subj + ' ' + s_dp[root_index][0].lower() + ' ' + xd_ct(s_dp, i) + ' làm gì?', vhccd(xd_ct(s_dp, j))])
                            theloai_cn = xd_nguoi_vat(xd_ct(s_dp, i))
                            loai = 'cái gì'
                            if theloai_cn == 0:
                                loai = 'ai'
                            elif theloai_cn == 1:
                                loai = 'con gì'
                            qa.append([s[:-1].replace(xd_ct(s_dp, i), loai) + '?', vhccd(xd_ct(s_dp, i))])
                        confirm_break = True
                        break
                if confirm_break:
                    break

                # Trường hợp vn_dongtu = 8: Sau root là 1 obj của root và 1 obj của comp. VD: Tôi mua hoa tặng mẹ.
                for j in range(i+1, len(s_dp)-1):
                    if s_dp[j][1] == root_index and 'comp' in s_dp[j][2] and s_dp[j][2] != 'ccomp' and s_dp[j][4] == 'B-VP':
                        for z in range(j+1, len(s_dp)-1):
                            if s_dp[z][1] == j and 'obj' in s_dp[z][2]:
                                vn_dongtu = 8
                                qa.append([subj + ' ' + s_dp[root_index][0].lower() + ' ' + xd_ct(s_dp, i) + ' làm gì?', vhccd(xd_ct(s_dp, j))])
                                theloai_cn = xd_nguoi_vat(xd_ct(s_dp, i))
                                loai = 'cái gì'
                                if theloai_cn == 0:
                                    loai = 'ai'
                                elif theloai_cn == 1:
                                    loai = 'con gì'
                                qa.append([s[:-1].replace(xd_ct(s_dp, i), loai) + '?', vhccd(xd_ct(s_dp, i))])
                                if s_dp[z][3] == 'Np' or s_dp[z][5] == 'B-PER':
                                    qa.append([subj + ' ' + s_dp[root_index][0].lower() + ' ' + xd_ct(s_dp, i) + ' ' + s_dp[j][0] + ' ai?', vhccd(xd_ct(s_dp, z))])        
                                confirm_break = True
                                break
                    if confirm_break:
                        break
                if confirm_break:
                    break


            # Trường hợp vn_dongtu = 9: Sau root là 1 obj.
            elif s_dp[i][1] == root_index and 'obj' in mqh:
                vn_dongtu = 9
                if s_dp[i][3] == 'Np' or s_dp[i][5] == 'B-PER':
                    qa.append([s[:-1].replace(xd_ct(s_dp[i][0]), 'ai') + '?', vhccd(xd_ct(s_dp, i))])
                else:
                    theloai_cn = xd_nguoi_vat(xd_ct(s_dp, i))
                    loai = 'cái gì'
                    if theloai_cn == 0:
                        loai = 'ai'
                    elif theloai_cn == 1:
                        loai = 'con gì'
                    qa.append([s[:-1].replace(xd_ct(s_dp[i][0]), loai) + '?', vhccd(xd_ct(s_dp, i))])
                break
            '''
            
        # Trường hợp cơ bản
        if vn_dongtu == 0:
            for i in range(root_index + 1, -1):
                if s_dp[i][4] != 'B-VP':
                    return 'SAI FORMAT'
            qa.append([subj + ' làm gì?', vhccd(xdccc(dongtu))])             
        qa.extend(bongu_mieuta(s, s_dp))
    return qa

def xuly_trangngu_daucau(s, s_dp):
    #s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            if s_dp[i][4] != 'B-VP':
                return 'SAI FORMAT'
            if root_index is None:
                root_index = i
            else:
                return 'SAI FORMAT'
            
    if root_index is None:
        return 'SAI FORMAT'
    
    # Check format: Trạng ngữ phải xuất hiện đầu câu
    tn_index = s_dp[root_index][6][0]
    if 'obl' not in s_dp[tn_index][2] and 'advcl' not in s_dp[tn_index][2]:
        return 'SAI FORMAT'
    
    # Tìm vị trí chủ ngữ
    cn_index = None
    for i in s_dp[root_index][6]:
        if i == root_index:
            break
        if 'subj' in s_dp[i][2]:
            if cn_index is not None:
                return 'SAI FORMAT'
            cn_index = i
            
    if cn_index is None:
        return 'SAI FORMAT'
    qa = []
   
    cum_tn = xd_ct(s_dp, tn_index)
    cum_cn = xd_ct(s_dp, cn_index)
    cn_index_last = s_dp[cn_index][6][-1]
    cum_vn = ''
    
    for i in range(cn_index_last+1, len(s_dp)-1):
        if s_dp[i][2] == 'punct':
            cum_vn += s_dp[i][0]
        else:
            cum_vn += ' ' + s_dp[i][0]
    cum_vn = cum_vn.strip()
    cau = cum_cn + ' ' + cum_vn
    dau = ''
    cau = vhccd(cau)
    cau_dp = dp_tree(cau)
    if cau[0] == ',':
        cau = cau.replace(',', '', 1)
        dau = ','
    if 'obl' in s_dp[tn_index][2]:
        list_obl = []
        dauphay_root_index = []
        # Check thành phần phía trước vị ngữ chỉ có trạng ngữ và chủ ngữ
        for i in s_dp[root_index][6]:
            if i == root_index:
                break
            if s_dp[i][2] != 'punct' and 'obl' not in s_dp[i][2] and 'subj' not in s_dp[i][2]:
                return 'SAI FORMAT'
            if 'obl' in s_dp[i][2]:
                list_obl.append(i)
            if s_dp[i][2] == 'punct':
                dauphay_root_index.append(i)
        if len(list_obl) >= 2:
            for i in list_obl[1:]:
                obl = xd_ct(s_dp, i)
                if obl[-1] == ',':
                    obl = obl[:-1]
                s = s.replace(' ' + obl, '')
                if s[-3:] == '...':
                    s = s[:-3] + ' ' + obl + '...'
                else:
                    s = s[:-1] + ' ' + obl + '.'
            
            for i in range(len(s)):
                s = s.replace(',,', ',')
            s_dp = dp_tree(s)
            return xuly_trangngu_daucau(s, s_dp)

    
        # Phát sinh câu hỏi 'Khi nào, ở đâu' 
        cau_cn_dongtu = temp_cn_dongtu(cau, cau_dp)
        cau_cn_tinhtu = temp_cn_tinhtu(cau, cau_dp)
        cau_cn_la_danhtu = temp_cn_la_danhtu(cau, cau_dp)
        if (cau_cn_dongtu != 'SAI FORMAT'):
            for j in range(len(cau_cn_dongtu)):
                qa.append([cum_tn + dau + ' ' + xvhccd(cau_cn_dongtu[j][0]), cau_cn_dongtu[j][1]])
        elif (cau_cn_tinhtu != 'SAI FORMAT'):
            for j in range(len(cau_cn_tinhtu)):
                qa.append([cum_tn + dau + ' ' + xvhccd(cau_cn_tinhtu[j][0]), cau_cn_tinhtu[j][1]])
        elif (cau_cn_la_danhtu != 'SAI FORMAT'):
            for j in range(len(cau_cn_la_danhtu)):
                qa.append([cum_tn + dau + ' ' + xvhccd(cau_cn_la_danhtu[j][0]), cau_cn_la_danhtu[j][1]])

        list_gt = []
        for i in range(tn_index):
            if s_dp[i][4] == 'B-PP':
                list_gt.append(i)
        if len(list_gt) >= 1:
            # Trường hợp có giới từ
            # Giới từ chỉ cách thức
            for i in list_gt:
                if s_dp[i][0].lower() == 'bằng':
                    qa.append(['Bằng cách nào ' + xvhccd(cau) + '?', cum_tn])

            # Giới từ chỉ nơi chốn
            set_gioitu_noichon = gioitu_noichon.split(', ')
            for i in list_gt:
                if s_dp[i][0].lower() in set_gioitu_noichon:
                    qa.append([cau + ' ở đâu?', cum_tn])
            # Giới từ chỉ thời gian
            set_gioitu_thoigian = gioitu_thoigian.split(', ')
            for i in list_gt:
                if s_dp[i][0].lower() in set_gioitu_thoigian:
                    qa.append(['Khi nào ' + xvhccd(cau) + '?', cum_tn])
        
        else:
            if 'tmod' in s_dp[tn_index][2]:
                for i in s_dp[tn_index][6]:
                    if s_dp[i][0].lower() == 'ngày':
                        qa.append(['Vào ngày mấy ' + xvhccd(cau) + '?', cum_tn])
                        return qa
                qa.append(['Khi nào ' + xvhccd(cau) + '?', cum_tn])
    else:
        cau_cn_dongtu = temp_cn_dongtu(cau, cau_dp)
        cau_cn_tinhtu = temp_cn_tinhtu(cau, cau_dp)
        cau_cn_la_danhtu = temp_cn_la_danhtu(cau, cau_dp)
        if (cau_cn_dongtu != 'SAI FORMAT'):
            for j in range(len(cau_cn_dongtu)):
                qa.append([cum_tn + dau + ' ' + xvhccd(cau_cn_dongtu[j][0]), cau_cn_dongtu[j][1]])
        elif (cau_cn_tinhtu != 'SAI FORMAT'):
            for j in range(len(cau_cn_tinhtu)):
                qa.append([cum_tn + dau + ' ' + xvhccd(cau_cn_tinhtu[j][0]), cau_cn_tinhtu[j][1]])
        elif (cau_cn_la_danhtu != 'SAI FORMAT'):
            for j in range(len(cau_cn_la_danhtu)):
                qa.append([cum_tn + dau + ' ' + xvhccd(cau_cn_la_danhtu[j][0]), cau_cn_la_danhtu[j][1]])
    return qa
# In[302]:


# temp_cn_dongtu('Tôi mua hoa tặng mẹ.')


# In[285]:


import string
# Tách câu ghép đẳng lập trong văn bản (quan hệ parataxis)
def tach_vecau(s):
    s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            root_index = i
            break
    if root_index is None:
        return [s]
    kq = []
    for i in s_dp[root_index][6]:
        if s_dp[i][2] == 'parataxis' or s_dp[i][2] == 'conj':
            for j in s_dp[i][6]:
                if 'subj' in s_dp[j][2]:
                    vecau = xd_ct(s_dp, i)
                    s = s.replace(vecau, '')
                    vecau = vecau.strip() + '.'
                    vecau_dp = dp_tree(vecau)
                    while vecau_dp[0][2] == 'cc' or vecau_dp[0][2] == 'punct':
                        vecau = vecau.replace(vecau_dp[0][0], '')
                        vecau_dp = dp_tree(vecau)
                    kq.append(vhccd(vecau.strip()))
                    break
                    
    kq.insert(0, removeSpaceFrontPunct(s))
    return kq


def tach_vecau_dauhaicham(s):
    s = s.split(':')
    for i in range(len(s)):
        s[i] = s[i].replace('\"', '')
        s[i] = s[i].replace("'", '')
        s[i] = s[i].replace("- ", '')
        s[i] = s[i].replace(".", '')
        if s[i] == '':
            s.pop(i)
        else:
            if s[i][-1] not in string.punctuation:
                s[i] = s[i].strip() + '.'
            s[i] = vhccd(s[i].strip())
    return s


# In[306]:


def loadFile(filename):
    lines = []
    count = 0
    with open(filename, 'r') as f:
        for para in f:
            st = sent_tokenize(para.strip())
            for s in st:
                if (s[-1] != '.'):
                    continue
                set_tach_hai_cham = tach_vecau_dauhaicham(s)
                for thc in set_tach_hai_cham:
                    thc = re.sub(r"\([^()]*\)", "", thc)
                    thc = thc.replace("(", "")
                    thc = thc.replace(")", "")
                    ve_cau = tach_vecau(thc)
                    lines.extend(ve_cau)
    return lines


# In[315]:


def loadTextarea(text):
    lines = []
    count = 0
    set_para = text.split('\n')
    for para in set_para:
        st = sent_tokenize(para.strip())
        for s in st:
            if (s[-1] != '.'):
                continue
            set_tach_hai_cham = tach_vecau_dauhaicham(s)
            for thc in set_tach_hai_cham:
                thc = re.sub(r"\([^()]*\)", "", thc)
                thc = thc.replace("(", "")
                thc = thc.replace(")", "")
                ve_cau = tach_vecau(thc)
                lines.extend(ve_cau)
    return lines


# In[316]:


def createQuestion(text):
    lines = loadTextarea(text)
    q = []
    loss = 0
    for l in lines:
        l_dp = dp_tree(l)
        kq = xuly_trangngu_daucau(l, l_dp)
        if kq != 'SAI FORMAT' and len(kq) > 0:
            q.append([l, kq])
            print(1)
        else:
            kq = temp_cn_dongtu(l, l_dp)
            if kq != 'SAI FORMAT' and len(kq) > 0:
                q.append([l, kq])
                print(2)
            else:
                kq = temp_cn_tinhtu(l, l_dp)
                if kq != 'SAI FORMAT' and len(kq) > 0:
                    q.append([l, kq])
                    print(3)
                else:
                    kq = temp_cn_la_danhtu(l, l_dp)
                    if kq != 'SAI FORMAT' and len(kq) > 0:
                        q.append([l, kq])
                    else:
                        loss += 1
    bad = 1
    if len(lines) > 0:
        bad = loss/len(lines)
    return (q, bad)

# In[317]:

if __name__ == '__main__':
    questions = createQuestion(sys.argv[1])
    q = questions[0]
    bad = questions[1]

    print('__result__')
    
    for i in q: 
        # Selected sentence
        print('\n',i[0])
        # Generated questions
        for j in i[1]:
            print('\t', j[0], '\t', j[1])




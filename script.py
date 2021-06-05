#!/usr/bin/env python
# coding: utf-8

# In[2]:


from underthesea import word_tokenize
from underthesea import pos_tag
from underthesea import sent_tokenize
from underthesea import dependency_parse
from underthesea import ner
from underthesea import classify
from underthesea import chunk

import random


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


# In[5]:


#TẠM THỜI KHÔNG LẤY BLOCK NÀY

#Xử lý trường hợp câu đơn với chủ ngữ là người/con vật
#Dạng câu hỏi: "Ai làm gì?" (S+V)
#Dạng câu hỏi: "Ai là gì?" (S+cop+N)
#Dạng câu hỏi: "Ai thế nào?" (S+A)
#Dạng câu hỏi: "Ai làm gì như thế nào?" (S+V+Adv/S+Adv+V)
def subject_root(s):
    s_ner = ner(s)
    s_dp = dependency_parse(s)
    root_index = None
    
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            root_index = i
            break
    # Chia trường hợp vị ngữ "làm gì?", "là gì?", "thế nào?"
    q_vingu = ''
    if s_ner[root_index][1] == 'V':
        q_vingu = 'làm gì?'
        # Trường hợp "làm gì như thế nào?"
        for i in range(len(s_dp)-1):
            if s_dp[i][1]-1 == root_index and s_dp[i][2] == 'acomp':
                q_vingu = 'như thế nào?'
                nhuthenao_index = i
                break
             
        # Xác định Ner LOC --> Câu hỏi "Đâu?"
        for i in range(root_index+1, len(s_dp)-1):
            if s_ner[i][3] == 'B-LOC' and s_dp[root_index][0] == 'đi':
                q_vingu = 'đâu?'
                where_index = i
                break
                
    elif s_ner[root_index][1] == 'A':
        q_vingu = 'thế nào?'
        
    elif s_ner[root_index][1] == 'N': # <Trường hợp câu có vị ngữ "là <Danh từ>">
        for i in range(root_index):
            if s_dp[i][0].lower() == 'là' and s_dp[i][1]-1 == root_index and s_dp[i][2] == 'cop':
                q_vingu = 'là ai?'
                root_index = i
                break
    else:
        print(s_ner[root_index][1])
        return
    
    q_ai = 'Ai'
    # Trường hợp đặc biệt
    # Ở vị trí Subject nếu có từ "con" là "det:clf" thì câu hỏi "Ai?" --> "Con gì?". Ngoại trừ trường hợp "Con gái", "Con trai"
    for i in range(root_index):
        if s_dp[i][0].lower() == 'con' and s_dp[i][2] == 'det:clf':
            # Parent of nsubj must be root
            nsubj_index = s_dp[i][1] - 1

            if s_dp[nsubj_index][1]-1 == root_index and                 s_dp[nsubj_index][0].lower() != 'gái' and                     s_dp[nsubj_index][0].lower() != 'trai':
                        q_ai = 'Con gì'
                        break
        # Công ty tổ chức (ORG-NER)
        if s_ner[i][3] == 'B-ORG':
            q_ai = 'Tổ chức nào'
    
    # Bước tạo câu hỏi cho từng dạng:
    r_ai = ''
    r_vn = ''
    q_vn = ''
    # Dạng 1: Ai làm gì? (S+V) và Ai là gì? (S+cop+N)
    if q_vingu == 'làm gì?' or q_vingu =='là ai?':
        # Tạo câu hỏi "Ai"
        for i in range(root_index, len(s_dp)-1):
            q_ai += ' ' + s_dp[i][0]
            r_vn += s_dp[i][0] + ' '
        q_ai += '?'
        
        # Tạo câu hỏi cho vị ngữ"
        for i in range(root_index):
            q_vn += s_dp[i][0] + ' '
            r_ai += s_dp[i][0] + ' '
        q_vn += q_vingu
        
    # Dạng 2: Ai làm gì như thế nào? (S+V+Adv)
    elif q_vingu == 'như thế nào?':
        # Tạo câu hỏi "Ai"
        for i in range(root_index, len(s_dp)-1):
            q_ai += ' ' + s_dp[i][0]
            if s_dp[i][1]-1 == root_index and s_dp[i][2] == 'acomp':
                r_vn += s_dp[i][0] + ' '
                # Kiểm tra còn từ nào liên quan với từ hiện tại không.
                for i in range(nhuthenao_index+1, len(s_dp)-1):
                    if s_dp[i][1]-1 == nhuthenao_index:
                        r_vn += s_dp[i][0] + ' '
                    
        q_ai += '?'
        
        # Tạo câu hỏi cho vị ngữ
        for i in range(nhuthenao_index):
            q_vn += s_dp[i][0] + ' '
            if i < root_index:
                r_ai += s_dp[i][0] + ' '
        q_vn += q_vingu
        
    # Dạng 3: Ai thế nào? (S+Adj)
    elif q_vingu == 'thế nào?':       
        # Tạo câu hỏi "Ai"     
        for i in range(root_index, len(s_dp)-1):
            q_ai += ' ' + s_dp[i][0]
            r_vn += s_dp[i][0] + ' '
        q_ai += '?'
        
        # Tạo câu hỏi cho vị ngữ
        for i in range(root_index):
            if s_dp[i][2] != 'advmod' or s_dp[i][1]-1 != root_index:
                q_vn += s_dp[i][0] + ' '
                r_ai += s_dp[i][0] + ' '
        q_vn += q_vingu
        
    # Dạng 4: Đâu? (LOC-NER)
    elif q_vingu == 'đâu?':       
        # Tạo câu hỏi "Ai"     
        for i in range(root_index, len(s_dp)-1):
            q_ai += ' ' + s_dp[i][0]
        q_ai += '?'
        
        # Tạo câu hỏi cho vị ngữ
        for i in range(root_index):
            r_ai += s_dp[i][0] + ' '
            
        for i in range(where_index, len(s_ner)-1):
            if s_ner[i][3] == 'B-LOC' or s_ner[i][3] == 'I-LOC':
                r_vn += ' ' + s_ner[i][0]
        q_vn = s.replace(r_vn.strip(), 'đâu')
        q_vn = q_vn.replace('.', '?')
        

    return [
        [q_ai, r_ai.strip().capitalize()],
        [q_vn, r_vn.strip().capitalize()]
    ]


# In[6]:


#TẠM THỜI KHÔNG LẤY BLOCK NÀY

# Câu đơn có trạng ngữ đứng đầu câu (Thời gian, nơi chốn)
# Xác định cụm trạng ngữ (Không được chứa cụm C-V, cuối trạng ngữ phải có dấu phẩy)
# Xác định cụm chủ ngữ
# Xác định cụm vị ngữ
# Điều kiện là các cụm phải liên tiếp với nhau

# Xử lý trường hợp câu đơn với trạng ngữ đứng đầu câu (Không tính cụm trạng ngữ nhiều loại)
# Dạng câu hỏi: "Khi nào/Lúc nào?"
# Dạng câu hỏi: "Ở đâu?"
def adverb_subject_root(s):
    s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            root_index = i
            break
    
    # Tìm vị trí của từng cụm trạng ngữ, chủ ngữ, vị ngữ
    t_index = None
    c_index = None
    v_index = root_index
    
    
    q_when = 'Khi nào'
    q_where = 'ở đâu'
    q_tn = ''
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'obl' or s_dp[i][2] == 'obl:tmod':
            t_index = i
            cum_tn = xd_ct(s_dp, t_index)
            # Kiểm tra trạng ngữ chỉ thời gian hay địa điểm
            if s_dp[i][2] == 'obl':
                q_tn = q_where
                if s_dp[i][0].lower() == 'thứ':
                    q_tn = q_when
                
            else:
                q_tn = q_when
                if s_dp[i][0].lower() == 'ngày':
                    q_tn = 'vào ngày mấy'
        elif s_dp[i][2] == 'nsubj':
            c_index = i
            cum_cn = xd_ct(s_dp, c_index)
    
    
    # Xác định cụm vị ngữ
    cum_vn = s.replace(cum_tn, '')
    cum_vn = cum_vn.replace(cum_cn, '')
    cum_vn = cum_vn[:-1]
    cum_vn = cum_vn.strip()
    
    Cn_Vn = cum_cn.capitalize() + ' ' + cum_vn + '.'
    q_Cn_Vn = subject_root(Cn_Vn)
    
    
    if q_tn == q_where:
        # CN + VN + ở đâu?
        q_tn = cum_cn.capitalize() + ' ' + cum_vn + ' ' + q_tn + '?' 
        r_tn = cum_tn.replace(',', '')
        
        # Ai + VN + TN?
        q_tmp = q_tn[0].lower() + q_tn[1:]
        q_Cn_Vn[0][0] = q_Cn_Vn[0][0][:-1] + ' ' + q_tmp + '?'
        
        # CN + làm gì/thế nào/là gì + TN?
        q_Cn_Vn[1][0] = q_Cn_Vn[1][0][:-1] + ' ' + q_tmp + '?'
        
    else:
        # Khi nào CN + VN?
        if q_tn == 'Khi nào':
            q_tn = q_tn + ' ' + cum_cn + ' ' + cum_vn + '?'
        else:
            q_tn = cum_cn.capitalize() + ' ' + cum_vn + ' ' + q_tn +'?'
        r_tn = cum_tn.replace(',', '')
        
        tu_noi_when = ''
        # Check xem trong cụm TN có từ khi/lúc/vào hay không.
        
        vao_tu_noi = []
        for i in range(len(cum_tn.split())):
            if (s_dp[i][0].lower() == 'ngày' and s_dp[i][2] == 'obl:tmod')             or s_dp[i][2] == 'flat:date' or s_dp[i][0].lower() == 'tháng' or s_dp[i][0].lower() == 'năm' or s_dp[i][0].lower() == 'tuần':
                tu_noi_when = 'vào'
                break
            elif s_dp[i][2] == 'flat:time':
                tu_noi_when = 'lúc'
                break
            else:
                tu_noi_when = 'khi'
                
        ignore_tu_noi = ['khi', 'vào', 'lúc', 'hôm nay', 'ngày mai', 'hôm qua']
        for i in ignore_tu_noi:
            if i in cum_tn.lower():
                tu_noi_when = ''
                
        # Ai + VN + khi/vào/lúc + TN?
        cum_tmp = cum_tn[0].lower() + cum_tn[1:-1]
        q_Cn_Vn[0][0] = q_Cn_Vn[0][0][:-1] + ' ' + tu_noi_when + ' ' + cum_tmp + '?'
        q_Cn_Vn[0][0] = " ".join(q_Cn_Vn[0][0].split())
    
        # CN + làm gì/thế nào/là gì + khi/vào/lúc + TN?
        q_Cn_Vn[1][0] = q_Cn_Vn[1][0][:-1] + ' ' + tu_noi_when + ' ' + cum_tmp + '?'
        q_Cn_Vn[1][0] = " ".join(q_Cn_Vn[1][0].split())
    
    q_Cn_Vn.append([q_tn, r_tn])
    return q_Cn_Vn


# In[7]:


#TẠM THỜI KHÔNG LẤY BLOCK NÀY

def filter_format(s):
    s_dp = dp_tree(s)
    
    if s[-1] != '.':
        return [False, False]
    elif s[-1] == '.' and s[-2] == '.':
        return [False, False]
    
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            if root_index is None:
                root_index = i
            # Kiểm tra xem có 2 root không
            else:
                return [False, False]
    
    # Kiểm tra có root không
    if root_index is None:
        return [False, False]
    
    
    childs_root_index = s_dp[root_index][-1]
    
    # Kiểm tra nhiều CN-VN
    nhieu_CN = False
    nhieu_VN = False
    for i in range(len(s_dp)):
        if i < root_index and s_dp[i][2] == 'conj':
            nhieu_CN = True
        elif i > root_index and s_dp[i][2] == 'conj' and s_dp[i][1] == root_index and len(s_dp[i][-1]) > 2:
            nhieu_VN = True
            
    
    CN_VN = False
    TN_CN_VN = False
    
    if s_dp[childs_root_index[0]][2] == 'nsubj' and     ((s_dp[childs_root_index[1]][2] == 'root' and (s_dp[childs_root_index[1]][3] == 'A' or s_dp[childs_root_index[1]][3] == 'V')) or      (s_dp[childs_root_index[2]][2] == 'root' and ((s_dp[childs_root_index[2]][3] == 'N' and s_dp[childs_root_index[1]][0] == 'là') or s_dp[childs_root_index[2]][3] == 'A'))):
        if not nhieu_CN and not nhieu_VN:
            CN_VN = True
    
    if (s_dp[childs_root_index[0]][2] == 'obl:tmod' or s_dp[childs_root_index[0]][2] == 'obl') and     s_dp[childs_root_index[1]][2] == 'nsubj' and     ((s_dp[childs_root_index[2]][2] == 'root' and (s_dp[childs_root_index[2]][3] == 'A' or s_dp[childs_root_index[2]][3] == 'V')) or      (s_dp[childs_root_index[3]][2] == 'root' and ((s_dp[childs_root_index[3]][3] == 'N' and s_dp[childs_root_index[2]][0] == 'là') or s_dp[childs_root_index[3]][3] == 'A'))):
        if not nhieu_CN and not nhieu_VN:
            TN_CN_VN = True
            
    return [CN_VN, TN_CN_VN]
        


# filename = 'testcase_caudon_s_root.txt'
# lines = []
# with open(filename,'r') as f:
#     for s in f:
#         # Tách câu
#         st = sent_tokenize(s.strip())
#         lines.extend(st)
# for l in lines:
#     qa = subject_root(l)
#     print(l, ' --- ', qa)

# filename = 'testcase_caudon_tn.txt'
# lines = []
# with open(filename,'r') as f:
#     for s in f:
#         # Tách câu
#         st = sent_tokenize(s.strip())
#         lines.extend(st)
# for l in lines:
#     qa = adverb_subject_root(l)
#     print(l, ' --- ', qa)

# print(dependency_parse('Tháng 7, Bác Hồ đọc bản tuyên ngôn độc lập.'))
# print(ner('8 giờ sáng ngày mai, Bác Hồ đọc bản tuyên ngôn độc lập.'))
# print(dependency_parse('3 giờ nữa, Bác Hồ đọc bản tuyên ngôn độc lập.'))
# print(ner('3 giờ nữa, Bác Hồ đọc bản tuyên ngôn độc lập.'))
# print(dependency_parse('Ngày mai, tôi được trở thành thầy giáo.'))
# print(ner('Ngày mai, tôi được trở thành thầy giáo.'))
# print(dependency_parse('Bác nông dân cày ruộng.'))
# print(ner('Bác nông dân cày ruộng.'))
# print(dependency_parse('Cái ghế nằm dưới góc nhà.'))
# print(ner('Cái ghế nằm dưới góc nhà.'))

# error = []
# for l in lines:
#     s_dp = dp_tree(l)
#     # Tìm vị trí root
#     for i in range(len(s_dp)):
#         if s_dp[i][2] == 'root':
#             root_index = i
#             break
#     s_new = xd_ct(s_dp, root_index)
#     print(l, ' --- ', s_new)
#     if l != s_new:
#         error.append(l)
# for i in error:
#     print(dp_tree(i))

# In[8]:


#TẠM THỜI KHÔNG LẤY BLOCK NÀY

# filename = 'data.txt'
# lines = []
# with open(filename,'r') as f:
#     for s in f:
#         # Tách câu
#         st = sent_tokenize(s.strip())
#         lines.extend(st)
# for l in lines:
#     check = filter_format(l)
#     if check[0]:
#         qa = subject_root(l)
#     elif check[1]:  
#         qa = adverb_subject_root(l)
#     else:
#         print(l, ' --- ', 'SAI FORMAT')
#         continue
#     print(l, ' --- ', qa)


# In[250]:


daitu = 'tôi, tao, ta, tớ, mình, chúng tôi, chúng ta, chúng tớ, chúng tao, chúng mình, bọn tao, bạn, các bạn, đằng ấy, mày, bọn mày, tên kia, anh, cậu, ông, gã, y, hắn, thằng, cô, chị, bà, ả, thị, cổ, bả, chúng nó, họ, bọn họ, bọn chúng, nó, bác, chú, mợ, dì, thím, nhân, dân, chủ, người, thầy, công, vợ, chồng, mẹ, cha, ba, tía, má, u, bầm, nữ, bố, trai, gái'

### TEMPLATE Chủ ngữ + là + danh từ 
def temp_cn_la_danhtu(s):
    s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            if s_dp[i][4] != 'B-NP':
                return 'SAI FORMAT'
            root_index = i
            break
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
                la_index = s_dp[root_index][6][1]
            else:
                return 'SAI FORMAT'
            
    if la_index is None:
        for i in range(s_dp[cn_index][6][-1] + 1, root_index):
            if 'NP' not in s_dp[i][4]:
                return 'SAI FORMAT'
        s = s.replace(vhccd(xd_ct(s_dp, cn_index)), vhccd(xd_ct(s_dp, cn_index)) + ' có')
        return temp_cn_dongtu(s)
    

   
    # Check format: Danh từ xuất hiện cuối câu, chỉ có danh từ là root.
    for i in range(la_index + 1, len(s_dp)-1):
        mqh = s_dp[i][2]
        if mqh == 'advcl' or mqh == 'parataxis'             or mqh == 'mark' or mqh == 'ccomp':
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
    danhtu = s.replace(subj + ' là ', '')
    
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
    
    return qa
    


# In[251]:


### TEMPLATE Chủ ngữ + (là) + tính từ
def temp_cn_tinhtu(s):
    s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            if s_dp[i][4] != 'B-AP':
                return 'SAI FORMAT'
            root_index = i
            break
    if root_index is None:
        return 'SAI FORMAT'
    
    # Check format: Chủ ngữ phải xuất hiện đầu câu, không thành phần phụ
    cn_index = s_dp[root_index][6][0]
    if 'subj' not in s_dp[cn_index][2]:
        return 'SAI FORMAT'

    # Check format: Tính từ xuất hiện cuối câu, chỉ có tính từ là root.
    last_cn_index = s_dp[cn_index][6][-1]
    for i in range(last_cn_index + 1, len(s_dp)-1):
        mqh = s_dp[i][2]
        if mqh == 'advcl' or mqh == 'parataxis'             or mqh == 'mark' or mqh == 'ccomp':
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
            for i in s_dp[cn_index][6]:
                # Trường hợp chủ ngữ là tên riêng PER (NER)
                if (s_dp[i][5] == 'B-PER'):
                    qa.append(['Ai ' + xdccc(tinhtu) + '?', subj])
                    break
                # Trường hợp chủ ngữ là tên địa danh LOC (NER)
                elif (s_dp[i][5] == 'B-LOC'):
                    qa.append(['Đâu là nơi ' + xdccc(tinhtu) + '?', subj])
                    break
            
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
    return qa


# In[301]:


dongtu_ymuon = 'toan, định, dám, chịu, buồn, nỡ, dự định, muốn, mong, chúc'
dongtu_batdau_tiepdien_ketthuc = 'bắt đầu, tiếp tục, hết, thôi, chuẩn bị'
### TEMPLATE Chủ ngữ + động từ
def temp_cn_dongtu(s):
    s_dp = dp_tree(s)
    root_index = None
    # Tìm vị trí root
    for i in range(len(s_dp)):
        if s_dp[i][2] == 'root':
            if s_dp[i][4] != 'B-VP':
                return 'SAI FORMAT'
            root_index = i
            break
    if root_index is None:
        return 'SAI FORMAT'
    
    # Check format: Chủ ngữ phải xuất hiện đầu câu, không thành phần phụ
    cn_index = s_dp[root_index][6][0]
    if 'subj' not in s_dp[cn_index][2]:
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
            for i in s_dp[cn_index][6]:
                # Trường hợp chủ ngữ là tên riêng PER (NER)
                if (s_dp[i][5] == 'B-PER'):
                    qa.append(['Ai ' + xdccc(dongtu) + '?', subj])
                    break
                # Trường hợp chủ ngữ là tên địa danh LOC (NER)
                elif (s_dp[i][5] == 'B-LOC'):
                    qa.append(['Đâu là nơi ' + xdccc(dongtu) + '?', subj])
                    break

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
            # Truong hop vn_dongtu = 1: Subj + V(root) + Subj + (V/N/A)(ccomp) + (obj)
            if s_dp[i][1] == root_index and mqh == 'ccomp' and 'subj' in s_dp[cn_index_ccomp][2]:
                vn_dongtu = 1
                bongu_ccomp = xd_ct(s_dp, i)
                pre_sent = s.replace(bongu_ccomp, '')
                pre_sent = pre_sent[:-1].strip()
                cn_dongtu = temp_cn_dongtu(bongu_ccomp)
                cn_tinhtu = temp_cn_tinhtu(bongu_ccomp)
                cn_la_danhtu = temp_cn_la_danhtu(bongu_ccomp)
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
                    qa.append([s[:-1].replace(s_dp[i][0], 'đâu') + '?', vhccd(xd_ct(s_dp, i))])
                else:
                    qa.append([s[:-1].replace(s_dp[i][0], 'gì') + '?', vhccd(xd_ct(s_dp, i))])
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
        # Trường hợp cơ bản
        if vn_dongtu == 0:
            for i in range(root_index + 1, -1):
                if s_dp[i][4] != 'B-VP':
                    return 'SAI FORMAT'
            qa.append([subj + ' làm gì?', vhccd(xdccc(dongtu))])             
        
    return qa


# In[302]:


temp_cn_dongtu('Tôi mua hoa tặng mẹ.')


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


# In[233]:


tach_vecau("Anh ấy đi du lịch và cô ấy đi làm.")


# In[71]:


tach_vecau_dauhaicham('Nóng trên mạng xã hội: Vui sao, nước mắt lại trào!.')


# In[199]:


temp_cn_dongtu("Anh ấy đi du lịch còn cô ấy đi làm.")


# In[281]:


tree = dp_tree("Tôi mua hoa tặng cho mẹ.")
for i in tree:
    print(i)


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
    
    st = sent_tokenize(text.strip())
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
    #lines = loadFile(filename)
    lines = loadTextarea(text)
    q = []
    loss = 0
    for l in lines:
        kq = temp_cn_dongtu(l)
        if kq != 'SAI FORMAT':
            q.append([l, kq])
        else:
            kq = temp_cn_tinhtu(l)
            if kq != 'SAI FORMAT':
                q.append([l, kq])
            else:
                kq = temp_cn_la_danhtu(l)
                if kq != 'SAI FORMAT':
                    q.append([l, kq])
                else:
                    loss += 1
    bad = loss/len(lines)
    return (q, bad)


# In[317]:


questions = createQuestion('Đất ở Việt Nam rất đa dạng, có độ phì cao, thuận lợi cho phát triển nông, lâm nghiệp. Việt Nam có hệ thực vật phong phú, đa dạng (khoảng 14 600 loài thực vật). Thảm thực vật chủ yếu là rừng rậm nhiệt đới, gồm các loại cây ưa ánh sáng, nhiệt độ lớn và độ ẩm cao.\nQuần thể động vật ở Việt Nam cũng phong phú và đa dạng, trong đó có nhiều loài thú quý hiếm được ghi vào Sách Đỏ của thế giới. Hiện nay, đã liệt kê được 275 loài thú có vú, 800 loài chim, 180 loài bò sát, 80 loài lưỡng thể, 2.400 loài cá, 5.000 loài sâu bọ. (Các rừng rậm, rừng núi đá vôi, rừng nhiều tầng lá là nơi cư trú của nhiều loài khỉ, voọc, vượn, mèo rừng. Các loài voọc đặc hữu của Việt Nam là voọc đầu trắng, voọc quần đùi trắng, voọc đen. Chim cũng có nhiều loài chim quý như trĩ cổ khoang, trĩ sao. Núi cao miền Bắc có nhiều thú lông dày như gấu ngựa, gấu chó, cáo, cầy...)\\nViệt Nam đã giữ gìn và bảo tồn một số vườn quốc gia đa dạng sinh học quý hiếm như Vườn quốc gia Hoàng Liên Sơn (khu vực núi Phan-xi-phăng, Lào Cai), Vườn quốc gia Cát Bà (Quảng Ninh), vườn quốc gia Cúc Phương (Ninh Bình),  vườn quốc gia  Phong Nha-Kẻ Bàng (Quảng Bình), vườn quốc gia Bạch Mã (Thừa Thiên Huế), vườn quốc gia Côn Đảo (đảo Côn Sơn, Bà Rịa-Vũng Tàu), vườn quốc gia Cát Tiên (Đồng Nai)… Các vườn quốc gia này là nơi cho các nhà sinh học Việt Nam và thế giới nghiên cứu khoa học, đồng thời là những nơi du lịch sinh thái hấp dẫn. Ngoài ra, UNESCO công nhận 8 khu dự trữ sinh quyển ở Việt Nam là khu dự trữ sinh quyển thế giới như Cần Giờ, Cát Tiên, Cát Bà, Châu thổ sông Hồng, Cù Lao Chàm, Vườn Quốc gia Mũi Cà Mau…')
q = questions[0]
bad = questions[1]


# In[318]:


# for i in q:
#     print(i[0], end='')
#     print(' -------- ', end='')
#     print(i[1])


# # In[273]:


# print(bad)


# # In[236]:


# for l in lines:
#     print(temp_cn_dongtu(l))


# # In[20]:


# print('Anh ấy nói: \"haha\".')


# # In[260]:


# a = re.sub(r"\([^()]*\)", "", "( Hom nay vui qua ) E may.")


# # In[261]:


# print(a)


# In[ ]:





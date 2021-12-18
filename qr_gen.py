#-*- coding:utf-8 -*-
# from enum import unique
# from re import A
from flask import Flask, app, render_template, request, url_for, send_file, flash, session
import os
import qrcode
import zipfile
from time import sleep
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import hashlib
import pymysql
from werkzeug.utils import escape, redirect
import db_conn

application = Flask(__name__)
application.secret_key = 'ABCDEFGHIJKL_Malden'

# 로그인 페이지 호출 START
@application.route("/")
def index():
  return render_template("Login.html")
# 로그인 페이지 호출 END


# 로그인 체크 START
@application.route("/login" , methods=['POST', 'GET'])
def login():
  if request.method == 'POST':
    str = ""
    salt = "malden"
    user_id = request.form['user_id']
    user_pw = request.form['user_pw']
    str = user_pw
    user_crypt = hashlib.sha512((str+salt).encode('utf8')).hexdigest()
    user_crypt2 = hashlib.sha512((user_crypt).encode('utf8')).hexdigest()

    db_conn.conn
    db_conn.curs

    table = "user_account"
    SELECT_sql = "select * from " + table + " where id = '"+user_id+"';"
    if db_conn.curs.execute(SELECT_sql) != "0":
      user_account_rows = db_conn.curs.fetchall()
      db_user_pw = user_account_rows[0]['password']
      print("user_crypt2 : "+user_crypt2)
      print("db_user_pw : "+db_user_pw)
      if user_crypt2 == db_user_pw:
        print("ok")
        session['userid'] = user_id
        return redirect('/qr_gen_box')
      else:
        print("wrong password")
        flash("아이디가 존재하지 않거나 비밀번호가 잘못되었습니다")
        return render_template("Login.html")
    else:
      print("err")
      flash("아이디가 존재하지 않거나 비밀번호가 잘못되었습니다")
      return render_template("Login.html")
# 로그인 체크 END


# 로그아웃 START
@application.route("/logout")
def logout():
  try:
    session.pop('userid', None)
    return redirect('/')
  except:
    session.pop('userid', None)
    return redirect('/')
# 로그아웃 END


# 로그인 성공시 QR코드 생성 페이지 호출 START
@application.route("/qr_gen_box")
def qr_gen_box():
  if 'userid' in session:
    session_user_id = '%s' % escape(session['userid'])
    return render_template("qr_gen_box.html", user_id = session_user_id)
  else:
    flash("로그인 후 이용가능합니다.")
    return redirect('/logout')
# 로그인 성공시 QR코드 생성 페이지 호출 END

# 외부(external) 서비스(manage 등)에서 접근시 QR코드 생성 페이지 호출 START
@application.route("/qr_gen_box_ext", methods=['POST', 'GET'])
def qr_gen_box_ext():
  if request.method == 'POST':
    user_id = request.form['session_user_id']
    user_pw = request.form['session_user_key']
    return_url = request.form['url']
    table = "user_account"
    SELECT_sql = "select user_num from " + table + " where id = '"+user_id+"' and password = '"+user_pw+"';"
    if db_conn.curs.execute(SELECT_sql) != "0":
      session['userid'] = user_id
      return render_template("qr_gen_box.html", user_id = request.form['session_user_id'])
    else:
     flash("잘못된 외부 접근입니다.\n다시 로그인해 주세요.")
     return redirect(return_url+'/logout')
  else:
    flash("잘못된 접근입니다.\n다시 로그인해 주세요.")
    return redirect('/logout')
# 외부(external) 서비스(manage 등)에서 접근시 QR코드 생성 페이지 호출 END

# box 단위 QR코드 생성 START
Size_id_list = ['XS_','S_','M_','L_','XL_','F_']
@application.route("/gen_box_complete", methods=['POST', 'GET'])
def gen_box_complete():
  selectedFont = ImageFont.truetype('./fonts/NanumBarunGothic.ttf',55)
  img_path = "./QR_Code_img/"
  img_format = ".PNG"
  QR_filename_list = []                                                     # 한 번에 생성된 QR 이미지명 저장
  
  unique_key, QR_count = 9, 0                                               # QR유니크 키, 한 번에 생성된 QR 개수

  if request.method == 'POST':
    if 'userid' in session:
      session_user_id = '%s' % escape(session['userid'])
      
      # user_num 호출 START
      db_conn.conn
      db_conn.curs
      table = "user_account"
      SELECT_sql = "select user_num from " + table + " where id = '"+session_user_id+"';"
      db_conn.curs.execute(SELECT_sql)
      user_num_rows = db_conn.curs.fetchall()
      db_user_num = user_num_rows[0]['user_num']
      user_num = db_user_num
      # user_num 호출 END
    else:
      flash("로그인 후 이용가능합니다.")
      return redirect('/logout')

    # QR 코드 생성 START
    def Make_QR(id_num, unique_key, QR_count):
      width_QR, total_height_QR = 0, 0                                      # 생성된 QR 너비, 전체 QR 세로
      no_ck_count = 0
      Size_and_Quantity, filename_Size = "", ""
      custom_prod_code = request.form['custom_prod_code_'+str(id_num)]
      product_name = request.form['product_name_'+str(id_num)]

      for Size_id in Size_id_list:
        try:
          Size_and_Quantity += request.form['ck_size_'+str(Size_id)+str(id_num)]+":"+request.form['Quantity_'+str(Size_id)+str(id_num)]
          Size_and_Quantity += ","
          filename_Size += request.form['ck_size_'+str(Size_id)+str(id_num)]
        except:
          no_ck_count += 1
          pass
      
      if no_ck_count < 6:
        # QR_Cord_Option START # (ERROR_CORRECT_ : L=7% M=15% Q=25% H=30%)
        qrc = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=15,
        border=1,
        )
        # QR_Cord_Option END #

        create_time = datetime.today().strftime("%y-%m-%d %H:%M:%S")
        result = ''
        
        result = create_time + '~' + custom_prod_code + '~' + Size_and_Quantity + '~' + str(unique_key)+ '~' + str(db_user_num) + '~' + 'B' # QR코드에 담길 값

        qrc.add_data(result)
        qrc.make()
        QR_img = qrc.make_image(fill_color="black", back_color="white")                                       # QR 코드 색상
        
        
        QR_filename = img_path+str(user_num)+'_'+custom_prod_code+'_'+filename_Size+'_'+str(QR_count)         # QR 파일명 선언
        QR_img.save(QR_filename+img_format)                                                                   # QR 코드 저장

        target_QRimg = Image.open(QR_filename+img_format).resize((560,560))                                   # QR 이미지 열기
        draw_QRimg = ImageDraw.Draw(target_QRimg)                                                             # 이미지 수정 모드
        width_QR = target_QRimg.width                                                                         # QR 이미지 너비
        height_QR = target_QRimg.height                                                                       # QR 이미지 높이
        prod_code_w, prod_code_h = draw_QRimg.textsize(custom_prod_code)                                      # 글자 너비 및 높이    
          
        product_name_text = product_name                                                                      # 상품명
        product_color_text = custom_prod_code[-4:]                                                            # 상품컬러

      # 상품 컬러 분석 START
        if custom_prod_code.find('BLACK') != -1:                                           
          product_color_text = "BLACK"
        elif custom_prod_code.find('RED') != -1:
          product_color_text = "RED"
        elif custom_prod_code.find('GRAY') != -1:
          product_color_text = "GRAY"
        elif custom_prod_code.find('ORANGE') != -1:
          product_color_text = "ORANGE"
        elif custom_prod_code.find('YELLOW') != -1:
          product_color_text = "YELLOW"
        elif custom_prod_code.find('GREEN') != -1:
          product_color_text = "GREEN"
        elif custom_prod_code.find('BLUE') != -1:
          product_color_text = "BLUE"
        elif custom_prod_code.find('NAVY') != -1:
          product_color_text = "NAVY"
        elif custom_prod_code.find('PURPLE') != -1:
          product_color_text = "PURPLE"
        elif custom_prod_code.find('KHAKI') != -1:
          product_color_text = "KHAKI"
        elif custom_prod_code.find('WHITE') != -1:
          product_color_text = "WHITE"
        elif custom_prod_code.find('BEIGE') != -1:
          product_color_text = "BEIGE"
        elif custom_prod_code.find('CHARCOAL') != -1:
          product_color_text = "CHARCOAL"
        elif custom_prod_code.find('PINK') != -1:
          product_color_text = "PINK"
        elif custom_prod_code.find('MUSTARD') != -1:
          product_color_text = "MUSTARD"
        elif custom_prod_code.find('CREAM') != -1:
          product_color_text = "CREAM"
        else:
          product_color_text = "NONE"

        if custom_prod_code.find('LIGHT') != -1:
          product_color_text = "LIGHT" + product_color_text
        if custom_prod_code.find('DARK') != -1:
          product_color_text = "DARK" + product_color_text
        if custom_prod_code.find('DEEP') != -1:
          product_color_text = "DEEP" + product_color_text
        if custom_prod_code.find('PASTEL') != -1:
          product_color_text = "PASTEL" + product_color_text
        if custom_prod_code.find('BRIGHT') != -1:
          product_color_text = "BRIGHT" + product_color_text
        if custom_prod_code.find('SKY') != -1:
          product_color_text = "SKY" + product_color_text                                 
      # 상품 컬러 분석 END

        total_height_QR = 1700
        canvasFORtext  =  Image.new("RGB", (width_QR, total_height_QR), (255,255,255) )
        draw_text  =  ImageDraw.Draw(canvasFORtext)

        draw_text.text((15, ((height_QR+30) - (prod_code_h*3))), product_name_text, fill=(0,0,0), font=selectedFont)                    # 상품명 넣기
        draw_text.text((15, ((height_QR+70) - prod_code_h)), product_color_text, fill=(0,0,0), font=selectedFont)                       # 상품 컬러 넣기
        draw_text.text((100, ((height_QR+200) - prod_code_h)), "사이즈   :   수량", fill=(0,0,0), font=ImageFont.truetype('./fonts/NanumBarunGothic.ttf',47))    # 사이즈 : 수량 넣기
        
        Vertical_Space = 265                                                                                                            # 사이즈 텍스트 세로 간격
        for Size_id in Size_id_list:
          try:
            Draw_Size, Draw_Quantity = "", ""
            Draw_Size = request.form['ck_size_'+str(Size_id)+str(id_num)]
            Draw_Separator = ":"
            Draw_Quantity = request.form['Quantity_'+str(Size_id)+str(id_num)]
            draw_text.text((145, ((height_QR+Vertical_Space) - prod_code_h)), Draw_Size, fill=(0,0,0), font=selectedFont)               # 사이즈 넣기 + 40
            draw_text.text((258, ((height_QR+Vertical_Space) - prod_code_h)), Draw_Separator, fill=(0,0,0), font=selectedFont)          # 구분자 넣기 + 105
            draw_text.text((320, ((height_QR+Vertical_Space) - prod_code_h)), Draw_Quantity, fill=(0,0,0), font=selectedFont)           # 수량 넣기 + 40
            Vertical_Space += 70
          except:
            pass

        canvasFORtext.save(QR_filename+'_text'+img_format)

        target_Logo = Image.open('Logo2'+img_format).resize((246,55))
        width_Logo = target_Logo.width
        height_Logo = target_Logo.height
        target_textimg = Image.open(QR_filename+'_text'+img_format)                                                 # 텍스트 이미지 열기
        target_result = Image.new("RGB", (width_QR, total_height_QR), (255,255,255))                                # 최종 QR 이미지 사이즈(한개)
        
        target_result.paste(target_textimg, (0,250))                                                                # (0,0) = 가로, 세로 / 텍스트 붙여넣기
        target_result.paste(target_QRimg, (0,250))                                                                  # QR코드 붙여넣기
        target_result.paste(target_Logo, (int((width_QR/2)-(width_Logo/2)),int((height_QR/2)-(height_Logo/2))+250)) # 로고 붙여넣기
        os.remove(str(QR_filename+img_format))
        os.remove(str(QR_filename+'_text'+img_format))
        target_result.save(QR_filename+img_format)                                                                  # 최종 QR 이미지 저장
        QR_filename_list.append(QR_filename+img_format)                                                             # 생성 리스트 항목에 파일명 추가
    # QR 코드 생성 END
      
      
    # A4 페이지에 QR 넣기 START
    def Make_Page(QR_filename_list, width_QR, total_height_QR, session_user_id):
      New_page = Image.new("RGB", (2480, 3508), (255,255,255))                         # A4용지 사이즈 (가로, 세로)
      create_time = datetime.today().strftime("%y-%m-%d %H%M%S")
      x, y, x_count, count, new_page_count = 30, 18, 1, 1, 1
      page_filename = img_path+session_user_id+'_'+create_time
      zip_list = []

      for QR_file in QR_filename_list:
        open_QRimg = Image.open(QR_file)                                               # 생성된 QR 이미지 열기
        New_page.paste(open_QRimg, (x,y))                                              # (0,0) = 가로, 세로 / QR 붙여넣기
        os.remove(QR_file)                                                             # A4에 붙여넣고 단일 QR 삭제
        x += width_QR + 60
        print("x_count : "+str(x_count))
        print("new_page_count : "+str(new_page_count))
        x_count += 1
        new_page_count += 1

        if x_count > 4:                                                                # QR 한 줄에 4개씩 넣기
          x, x_count = 30, 1
          y += total_height_QR

        if new_page_count % 9 == 0:                                                    # QR 8개 이상 -> 페이지 추가 생성
          New_page.save(str(page_filename)+'_'+str(count)+img_format)
          count += 1
          print("count : "+str(count))
          x, y, x_count, new_page_count = 30, 18, 1, 1
          New_page = Image.new("RGB", (2480, 3508), (255,255,255))                     
      
      New_page.save(str(page_filename)+'_'+str(count)+img_format)
      zip_list.append(str(page_filename)+'_'+str(count)+img_format)

      return zip_list 
      
    # A4 페이지에 QR 넣기 END
      


    id_num_array = request.form['id_num_array'].split(',')  # 생성된 div_form 개수
    for id_num in id_num_array:
      unique_key += 1
      QR_count += 1
      Make_QR(str(id_num), int(unique_key), int(QR_count))
    
    page_zip_list = Make_Page(QR_filename_list, 560, 1700, session_user_id)
    # 파일 압축 start #
    create_time = datetime.today().strftime("%y%m%d%H%M%S")   
    zip_name = img_path+session_user_id+'_'+create_time+'.zip'
    with zipfile.ZipFile(zip_name, 'w') as myzip:
      for z in page_zip_list:
        myzip.write(str(z))
    # 파일 압축 end #

    
    for z in page_zip_list:                                                      # 압축 후 원본 page파일 삭제 #
      os.remove(str(z))   
    

  else:                                                       
    if 'userid' in session:
      session_user_id = '%s' % escape(session['userid'])
      flash("잘못된 접근입니다. 다시 시도해주세요.")
      return redirect('/logout')
    else:
      flash("로그인 후 이용가능합니다.")
      return redirect('/')

  return send_file(zip_name,as_attachment=True) # 생성된 압축 파일 다운로드 폴더에 저장
  # return render_template("qr_gen_box.html", user_id = session_user_id)
# box 단위 QR코드 생성 END #


######################################################################################


# 단일 QR코드 생성 START #
@application.route("/gen_complete", methods=['POST', 'GET'])
def gen_complete_main():
  selectedFont = ImageFont.truetype('./fonts/NanumBarunGothic.ttf',55)
  QR_count_tmp = 0
  id_num_array = []
  if request.method == 'POST':
    if 'userid' in session:
      session_user_id = '%s' % escape(session['userid'])
      
      # user_num 호출 START
      db_conn.conn
      db_conn.curs
      table = "user_account"
      SELECT_sql = "select user_num from " + table + " where id = '"+session_user_id+"';"
      db_conn.curs.execute(SELECT_sql)
      user_num_rows = db_conn.curs.fetchall()
      db_user_num = user_num_rows[0]['user_num']
      user_num = db_user_num
      # user_num 호출 END
    else:
      flash("로그인 후 이용가능합니다.")
      return redirect('/logout')


    img_path = "./QR_Code_img/"
    img_format = ".PNG"
    zip_list, zip_name, zip_name_tmp, zip_add_size = [], '', '', ''
    custom_prod_code = request.form['custom_prod_code']
    product_name = request.form['product_name']
    Quantity = request.form['Quantity']
    zip_name_tmp = img_path+custom_prod_code    
    unique_key = 0  # 중복 방지 키 값

    arr = []
    if request.form['size_XS'] != 'False':
      arr.append(request.form['size_XS'])

    if request.form['size_S'] != 'False':
      arr.append(request.form['size_S'])

    if request.form['size_M'] != 'False':
      arr.append(request.form['size_M'])

    if request.form['size_L'] != 'False':
      arr.append(request.form['size_L'])
    
    if request.form['size_XL'] != 'False':
      arr.append(request.form['size_XL'])

    if request.form['size_F'] != 'False':
      arr.append(request.form['size_F'])

    

    def Make_QR(id_num):
      create_time = datetime.today().strftime("%y-%m-%d %H:%M:%S")
      result = ''
      result = create_time + '~' + custom_prod_code + '~' + Size + '~' + str(unique_key) # QR코드에 담길 값

      # QR_Cord_Option START # (ERROR_CORRECT_ : L=7% M=15% Q=25% H=30%)
      qrc = qrcode.QRCode(
      version=1,
      error_correction=qrcode.constants.ERROR_CORRECT_Q,
      box_size=12,
      border=1,
      )
      # QR_Cord_Option END #
      target_QRimg, target_textimg, target_result, QR_img, width_QR, height_QR, w, h = None, None, None, None, 0, 0, 0, 0
      QR_count = 0
      qrc.add_data(result)
      qrc.make()
      QR_img = qrc.make_image(fill_color="black", back_color="white")               # QR 코드 색상
      QR_img.save(filename+str(img_format))                                         # QR 코드 저장
      
      ####################### QR_Design START #######################
      target_QRimg = Image.open(filename+str(img_format))                                           # QR이미지 열기
      draw_QRimg = ImageDraw.Draw(target_QRimg)                                     # 이미지 수정 모드
      prod_code_w, prod_code_h = draw_QRimg.textsize(custom_prod_code)              # 글자 크기    
      width_QR = target_QRimg.width                                                 # 이미지 크기
      height_QR = target_QRimg.height
        
      product_name_text = product_name                                              # 상품명
      product_color_text = custom_prod_code[-4:]                                    # 상품컬러

      # 상품 컬러 분석 START
      if custom_prod_code.find('BLACK') != -1:                                           
        product_color_text = "BLACK"
      elif custom_prod_code.find('RED') != -1:
        product_color_text = "RED"
      elif custom_prod_code.find('GRAY') != -1:
        product_color_text = "GRAY"
      elif custom_prod_code.find('ORANGE') != -1:
        product_color_text = "ORANGE"
      elif custom_prod_code.find('YELLOW') != -1:
        product_color_text = "YELLOW"
      elif custom_prod_code.find('GREEN') != -1:
        product_color_text = "GREEN"
      elif custom_prod_code.find('BLUE') != -1:
        product_color_text = "BLUE"
      elif custom_prod_code.find('NAVY') != -1:
        product_color_text = "NAVY"
      elif custom_prod_code.find('PURPLE') != -1:
        product_color_text = "PURPLE"
      elif custom_prod_code.find('KHAKI') != -1:
        product_color_text = "KHAKI"
      elif custom_prod_code.find('WHITE') != -1:
        product_color_text = "WHITE"
      elif custom_prod_code.find('BEIGE') != -1:
        product_color_text = "BEIGE"
      elif custom_prod_code.find('CHARCOAL') != -1:
        product_color_text = "CHARCOAL"
      elif custom_prod_code.find('PINK') != -1:
        product_color_text = "PINK"
      elif custom_prod_code.find('MUSTARD') != -1:
        product_color_text = "MUSTARD"
      elif custom_prod_code.find('CREAM') != -1:
        product_color_text = "CREAM"
      else:
        product_color_text = "NONE"

      if custom_prod_code.find('LIGHT') != -1:
        product_color_text = "LIGHT" + product_color_text
      if custom_prod_code.find('DARK') != -1:
        product_color_text = "DARK" + product_color_text
      if custom_prod_code.find('DEEP') != -1:
        product_color_text = "DEEP" + product_color_text
      if custom_prod_code.find('PASTEL') != -1:
        product_color_text = "PASTEL" + product_color_text
      if custom_prod_code.find('BRIGHT') != -1:
        product_color_text = "BRIGHT" + product_color_text
      if custom_prod_code.find('SKY') != -1:
        product_color_text = "SKY" + product_color_text                                 
      # 상품 컬러 분석 END

      total_height_QR = height_QR+50
      canvasFORtext  =  Image.new("RGB", (width_QR, total_height_QR), (255,255,255) )
      draw_text  =  ImageDraw.Draw(canvasFORtext)
      # draw_text_w, draw_text_h = draw_text.textsize(product_name_text.encode("UTF-8"))
      # draw_text_w2, draw_text_h2 = draw_text.textsize(product_color_text+Size)

      draw_text.text((10, (height_QR+33 - (prod_code_h*3))), product_name_text, fill=(0,0,0), font=selectedFont)          # Draw product_name
      draw_text.text((10, (height_QR+35 - prod_code_h)), product_color_text+' / '+Size, fill=(0,0,0), font=selectedFont)  # Draw Product_color
      canvasFORtext.save(filename+'_text'+img_format)

      target_Logo = Image.open('Logo2'+img_format)
      width_Logo = target_Logo.width
      target_textimg = Image.open(filename+'_text'+img_format)                              # 텍스트 이미지 열기
      target_result = Image.new("RGB", (width_QR, total_height_QR), (255,255,255))
      # target_result = Image.new("RGB", (2480, 3508), (255,255,255))                         # A4용지 사이즈 (가로, 세로)
      target_result.paste(target_textimg, (0,0))                                            # (0,0) = 가로, 세로 / 텍스트 붙여넣기
      target_result.paste(target_QRimg, (0,0))                                              # QR코드 붙여넣기
      # target_result.paste(target_Logo, (int((width_QR/2)-(width_Logo/2)),int(height_QR/2))) # 로고 붙여넣기
      os.remove(str(filename+'_text'+img_format))

      # target_result.save(filename)
      QR_count = Make_Page(create_time, width_QR, total_height_QR, int(file_count))
      return QR_count
      ####################### QR_Design END #######################

    div_form_count = int(request.form['div_form_count'])
    id_num_array = request.form['id_num_array'].split(',')
    for id_num in id_num_array:
      Make_QR(id_num)


    def Make_Page(create_time, sample_width_QR, sample_height_QR, file_count):
      page_result = Image.new("RGB", (2480, 3508), (255,255,255))                         # A4용지 사이즈 (가로, 세로)
      unique_key = 9
      page_x, page_y, interval_x, interval_y = 30, 200, 60, 180

      for h in range(200, 3508, sample_height_QR + interval_y):
        if page_y + sample_height_QR < 3508:
          page_x = 30
          for w in range(30, 2480, sample_width_QR + interval_x):
            if page_x + sample_width_QR < 2480:
              current_time = datetime.today().strftime("%y-%m-%d %H:%M:%S")
              if unique_key > 98:
                sleep(1)
                current_time = datetime.today().strftime("%y-%m-%d %H:%M:%S")
                unique_key = 10
              else:
                unique_key = unique_key + 1

              result2 = current_time + '~' + custom_prod_code + '~' + Size + '~' + str(unique_key) # QR코드에 담길 값
              # QR_Cord_Option START # (ERROR_CORRECT_ : L=7% M=15% Q=25% H=30%)
              qrc = qrcode.QRCode(
              version=1,
              # error_correction=qrcode.constants.ERROR_CORRECT_M,
              # box_size=14,
              error_correction=qrcode.constants.ERROR_CORRECT_Q,
              box_size=12,
              border=1,
              )
              # QR_Cord_Option END #
              target_QRimg, target_textimg, target_result, QR_img, width_QR, height_QR, w, h = None, None, None, None, 0, 0, 0, 0
              qrc.add_data(result2)
              qrc.make()
              QR_img = qrc.make_image(fill_color="black", back_color="white")               # QR 코드 색상
              QR_img.save(filename+str(img_format))                                                         # QR 코드 저장
              
              ####################### QR_Design START #######################
              target_QRimg = Image.open(filename+str(img_format))                                           # QR이미지 열기
              draw_QRimg = ImageDraw.Draw(target_QRimg)                                     # 이미지 수정 모드
              prod_code_w, prod_code_h = draw_QRimg.textsize(custom_prod_code)              # 글자 크기    
              width_QR = target_QRimg.width                                                 # 이미지 크기
              height_QR = target_QRimg.height
                
              product_name_text = product_name                                              # 상품명
              product_color_text = custom_prod_code[-4:]                                    # 상품컬러

            # 상품 컬러 분석 START
              if custom_prod_code.find('BLACK') != -1:                                           
                product_color_text = "BLACK"
              elif custom_prod_code.find('RED') != -1:
                product_color_text = "RED"
              elif custom_prod_code.find('ORANGE') != -1:
                product_color_text = "ORANGE"
              elif custom_prod_code.find('YELLOW') != -1:
                product_color_text = "YELLOW"
              elif custom_prod_code.find('GREEN') != -1:
                product_color_text = "GREEN"
              elif custom_prod_code.find('BLUE') != -1:
                product_color_text = "BLUE"
              elif custom_prod_code.find('NAVY') != -1:
                product_color_text = "NAVY"
              elif custom_prod_code.find('PURPLE') != -1:
                product_color_text = "PURPLE"
              elif custom_prod_code.find('KHAKI') != -1:
                product_color_text = "KHAKI"
              elif custom_prod_code.find('WHITE') != -1:
                product_color_text = "WHITE"
              elif custom_prod_code.find('BEIGE') != -1:
                product_color_text = "BEIGE"
              elif custom_prod_code.find('CHARCOAL') != -1:
                product_color_text = "CHARCOAL"
              elif custom_prod_code.find('PINK') != -1:
                product_color_text = "PINK"
              else:
                product_color_text = "NONE"

              if custom_prod_code.find('LIGHT') != -1:
                product_color_text = "LIGHT" + product_color_text
              if custom_prod_code.find('DARK') != -1:
                product_color_text = "DARK" + product_color_text
              if custom_prod_code.find('DEEP') != -1:
                product_color_text = "DEEP" + product_color_text
              if custom_prod_code.find('PASTEL') != -1:
                product_color_text = "PASTEL" + product_color_text                                
            # 상품 컬러 분석 END

              total_height_QR = height_QR+110
              canvasFORtext  =  Image.new("RGB", (width_QR, total_height_QR), (255,255,255) )
              draw_text  =  ImageDraw.Draw(canvasFORtext)

              draw_text.text((10, (height_QR+33 - (prod_code_h*3))), product_name_text, fill=(0,0,0), font=selectedFont)          # Draw product_name
              draw_text.text((10, (height_QR+70 - prod_code_h)), product_color_text+' / '+Size, fill=(0,0,0), font=selectedFont)  # Draw Product_color
              canvasFORtext.save(filename+'_text'+img_format)

              target_Logo = Image.open('Logo2'+img_format).resize((216,45))
              width_Logo = target_Logo.width
              height_Logo = target_Logo.height
              target_textimg = Image.open(filename+'_text'+img_format)                              # 텍스트 이미지 열기
              target_result = Image.new("RGB", (width_QR, total_height_QR), (255,255,255))
              target_result.paste(target_textimg, (0,0))                                            # (0,0) = 가로, 세로 / 텍스트 붙여넣기
              target_result.paste(target_QRimg, (0,0))                                              # QR코드 붙여넣기
              target_result.paste(target_Logo, (int((width_QR/2)-(width_Logo/2)),int((height_QR/2)-(height_Logo/2)))) # 로고 붙여넣기
              # target_result.paste(target_Logo, (int((width_QR)-(width_Logo+10)),int((height_QR)-(height_Logo+10)))) # 로고 붙여넣기
              os.remove(str(filename+'_text'+img_format))
              target_result.save(filename + str(unique_key) + str(img_format))

              QR_piece = Image.open(filename + str(unique_key) + str(img_format))
              page_result.paste(QR_piece,(page_x,page_y))
              os.remove(filename + str(unique_key) + str(img_format))
              page_x = int(page_x) + int(sample_width_QR) + int(interval_x)

              print("unique_key : "+str(unique_key))
            else:
              print("complete x")

          print("unique_key : "+str(unique_key))
          page_y = int(page_y) + int(sample_height_QR) + int(interval_y)
          
        else:
          print("complete y")

      page_result.save(filename + '_' + str(file_count) + str(img_format))
      return unique_key

    for i in arr:
        result, Size, filename, file_count = '', '', '', 1
        Size = str(i)
        filename = img_path+custom_prod_code+'-'+Size                                     # 파일명 선언
        QR_count_tmp = Make_QR(int(file_count))                                           # QR코드 생성 함수 호출
        os.remove(str(filename + '_' + str(file_count) + str(img_format)))                # 샘플 파일 삭제

        # 수량 체크 START
        if Quantity == '':
          Quantity = 0

        if int(int(Quantity) % (QR_count_tmp - 9)) == 0 and int(Quantity) != 0:
          for a in range(int(int(Quantity) / (QR_count_tmp - 9))):
            Make_QR(int(file_count))
            zip_list.append(filename + '_' + str(file_count) + str(img_format))           # 압축 파일 리스트 생성
            file_count = file_count + 1
            # print("makekekekeke!")
            sleep(0.6)
        else:
          for a in range(int(int(Quantity) / (QR_count_tmp - 9))+1):
            Make_QR(int(file_count))
            zip_list.append(filename + '_' + str(file_count) + str(img_format))           # 압축 파일 리스트 생성
            file_count = file_count + 1
            # print("makekekekeke!")
            sleep(0.6)
        # 수량 체크 END
        
        os.remove(str(filename+img_format))                                               # 샘플 파일 삭제
        zip_add_size += str(i)
        
    # 파일 압축 start #    
    zip_name = zip_name_tmp + '_' + zip_add_size + '_' + datetime.today().strftime("%y%m%d%H%M%S") + '.zip'
    with zipfile.ZipFile(zip_name, 'w') as myzip:
      for z in zip_list:
        myzip.write(str(z))
    # 파일 압축 end #

    # 압축 후 원본파일 삭제 start #
    for z in zip_list:
      os.remove(str(z))
    # 압축 후 원본파일 삭제 end #
  
  else:                                                       
    if 'userid' in session:
      session_user_id = '%s' % escape(session['userid'])
      flash("잘못된 접근입니다. 다시 시도해주세요.")
      return redirect('/logout')
    else:
      flash("로그인 후 이용가능합니다.")
      return redirect('/')
      
  return send_file(zip_name,as_attachment=True) # 생성된 압축 파일 다운로드 폴더에 저장    
    
  

if __name__ == "__main__":
    application.run(host='0.0.0.0')
    # application.run(debug=True)

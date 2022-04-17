from back_translators import GoogleBackTranslator
GBT = GoogleBackTranslator('en', use_googletrans=False)

def back_trans_col_based(f_path, col_num=0):
  '''
  A method to back translate text files before put into BERT. This
  method will back translate the value of specified column number 
  leaving other columns values unchanged.
  
  Parameters:
  f_path: path of the input text file (i.e., /data/train.txt).
  col_num: the column number that need back translation, default=0.

  Output:
  <file_name>_trans.txt file in the same directory of the input file.
  '''
  
  #read the input file (i.e., train.txt).
  file = open(f_path, "r")
  lines = file.readlines()
  file.close()
  
  translated_lines = []
  for line in lines:
    left, right, label = line.split("\t")
    transd_l = val_trans(left, col_num)
    transd_r = val_trans(right, col_num)
    transd_line = "\t".join([transd_l, transd_r, label])
    translated_lines.append(transd_line)

  #Concatenate lines with translated lines to increase the size of the training set.
  #lines[-1] = lines[-1] + "\n"
  #translated_lines[-1] = translated_lines[-1] + "\n" 
  new_lines = lines + translated_lines

  #check and clean potential character '\u200b' that 'gbk' codec can't encode.
  for i in range(len(new_lines)):
    new_lines[i] = new_lines[i].replace("\u200b", "")

  #write a new file named <file_name>_trans.txt in the same directory.
  file = open(f_path.partition(".txt")[0] + "_trans.txt", "w")
  file.writelines(new_lines)
  file.close()

def val_trans(in_str, col_num):
  #Continue to split until we get the VAL to translate.
  val_splitted = in_str.split("VAL")
  if col_num < len(val_splitted)-2:
    col_splitted = val_splitted[col_num+1].split("COL")
    str2translate = col_splitted[0]
  else:
    str2translate = val_splitted[-1]
  
  str_translated = " " + GBT.back_translate(str2translate, mid_lang='fr') + " "

  #Join all splitted elements back to original list format with special tokens included.
  if col_num < len(val_splitted)-2:
    col_splitted[0] = str_translated
    col2replace = "COL".join(col_splitted)
    val_splitted[col_num+1] = col2replace
  else:
    val_splitted[-1] = str_translated
  return "VAL".join(val_splitted)

if __name__ == "__main__":
  back_trans_col_based("AGtrain.txt")
  back_trans_col_based("DBLP-ACMtrain.txt")
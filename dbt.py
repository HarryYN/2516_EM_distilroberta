from back_translators import GoogleBackTranslator
GBT = GoogleBackTranslator('en', use_googletrans=False)

def back_trans_col_based(f_path, col_num=0, subset_size=50):
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
  transd_ls = []
  transd_rs = []
  lines_l = []
  lines_r = []

  for line in lines:
    left, right, label = line.split('\t')
    lines_l.append(left.split("VAL")[col_num+1].split("COL")[0])
    lines_r.append(right.split("VAL")[col_num+1].split("COL")[0])

  #translation step
  subsets_l = [lines_l[x:x+subset_size] for x in range(0, len(lines_l), subset_size)]
  subsets_r = [lines_r[x:x+subset_size] for x in range(0, len(lines_r), subset_size)]
  for i in range(len(subsets_l)):
    transd_ls += subset_back_translate(subsets_l[i])
    transd_rs += subset_back_translate(subsets_r[i])
    print("processing subset", i+i*(subset_size-1), "to", i+(i+1)*(subset_size-1))

  for i in range(len(lines)):
    left, right, label = lines[i].split('\t')
    transd_l = replace_val(left, col_num, transd_ls[i] + " ")
    transd_r = replace_val(right, col_num, transd_rs[i] + " ")
    transd_line = "\t".join([transd_l, transd_r, label])
    translated_lines.append(transd_line)

  #Concatenate lines with translated lines to increase the size of the training set.
  new_lines = lines + translated_lines

  #check and clean potential character '\u200b' that 'gbk' codec can't encode.
  for i in range(len(new_lines)):
      new_lines[i] = new_lines[i].replace("\u200b", "")

  #write a new file named <file_name>_trans.txt in the same directory.
  file = open(f_path.partition(".txt")[0] + "_trans.txt", "w")
  file.writelines(new_lines)
  file.close()

def subset_back_translate(subset):
  str2translate = "\n\n\n".join(subset)
  transd_str = GBT.back_translate(str2translate, mid_lang='vi')
  transd_subset = transd_str.split("\n\n\n")
  transd_subset[0] = " " + transd_subset[0]
  return transd_subset

def replace_val(in_str, col_num, dst_str):
  #Continue to split until we get the VAL to translate.
  val_splitted = in_str.split("VAL")
  if col_num < len(val_splitted)-2:
    col_splitted = val_splitted[col_num+1].split("COL")
    col_splitted[0] = dst_str
  else:
    val_splitted[-1] = dst_str

  #Join all splitted elements back to original list format with special tokens included.
  if col_num < len(val_splitted)-2:
    col2replace = "COL".join(col_splitted)
    val_splitted[col_num+1] = col2replace
  return "VAL".join(val_splitted)

if __name__ == "__main__":
  back_trans_col_based("train.txt")

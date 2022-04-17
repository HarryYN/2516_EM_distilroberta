import torch

from torch.utils import data
from transformers import AutoTokenizer

from .augment import Augmenter

# map lm name to huggingface's pre-trained model names
lm_mp = {'roberta': 'roberta-base',
         'distilbert': 'distilbert-base-uncased'}

def get_tokenizer(lm):
    if lm in lm_mp:
        return AutoTokenizer.from_pretrained(lm_mp[lm])
    else:
        return AutoTokenizer.from_pretrained(lm)


class DittoDataset(data.Dataset):
    """EM dataset"""

    def __init__(self,
                 path,
                 max_len=256,
                 size=None,
                 lm='roberta',
                 da=None):
        self.tokenizer = get_tokenizer(lm)
        self.pairs = []
        self.labels = []
        self.max_len = max_len
        self.size = size

        if isinstance(path, list):
            lines = path
        else:
            lines = open(path)

        for line in lines:
            s1, s2, label = line.strip().split('\t')
            self.pairs.append((s1, s2))
            self.labels.append(int(label))

        self.pairs = self.pairs[:size]
        self.labels = self.labels[:size]
        self.da = da
        if da is not None:
            self.augmenter = Augmenter()
        else:
            self.augmenter = None


    def __len__(self):
        """Return the size of the dataset."""
        return len(self.pairs)

    def __getitem__(self, idx):
        """Return a tokenized item of the dataset.

        Args:
            idx (int): the index of the item

        Returns:
            List of int: token ID's of the two entities
            List of int: token ID's of the two entities augmented (if da is set)
            int: the label of the pair (0: unmatch, 1: match)
        """
        left = self.pairs[idx][0]
        right = self.pairs[idx][1]

        # left + right
        x = self.tokenizer(text=left,
                           text_pair=right,
                            max_length=self.max_len,
                            truncation=True)

        # augment if da is set
        if self.da is not None:
            combined = self.augmenter.augment_sent(left + ' [SEP] ' + right, self.da)
            left, right = combined.split(' [SEP] ')
            x_aug = self.tokenizer(text=left,
                                    text_pair=right,
                                    max_length=self.max_len,
                                    truncation=True)
            return x, x_aug, self.labels[idx]
        else:
            return x, self.labels[idx]


    @staticmethod
    def pad(batch):
        """Merge a list of dataset items into a train/test batch
        Args:
            batch (list of tuple): a list of dataset items

        Returns:
            LongTensor: x1 of shape (batch_size, seq_len)
            LongTensor: x2 of shape (batch_size, seq_len).
                        Elements of x1 and x2 are padded to the same length
            LongTensor: a batch of labels, (batch_size,)
        """
        if len(batch[0]) == 3:
            x1_dic, x2_dic, y = zip(*batch)
            #x1=x1_dic['input_ids']
            #x1_mask=x1_dic['attention_mask']
            #x2=x2_dic['input_ids']
            #x2_mask=x2_dic['attention_mask']

            #对id进行padding
            maxlen = max([len(x['input_ids']) for x in x1_dic+x2_dic])
            x1 = [xi['input_ids'] + [0]*(maxlen - len(xi['input_ids'])) for xi in x1_dic]
            x2 = [xi['input_ids'] + [0]*(maxlen - len(xi['input_ids'])) for xi in x2_dic]

            #对mask进行padding
            x1_mask = [xi['attention_mask'] + [0]*(maxlen - len(xi['attention_mask'])) for xi in x1_dic]
            x2_mask = [xi['attention_mask'] + [0]*(maxlen - len(xi['attention_mask'])) for xi in x2_dic]

            return torch.LongTensor(x1), \
                   torch.LongTensor(x1_mask),\
                   torch.LongTensor(x2), \
                   torch.LongTensor(x2_mask),\
                   torch.LongTensor(y)
        else:
            #这里的x12_dic是一个字典的元组
            x12_dic, y = zip(*batch)
            #x12=x12_dic['input_ids']
            #x12_mask=x12_dic['attention_mask']
            maxlen = max([len(x['input_ids']) for x in x12_dic])
            #对encoding 进行padding
            x12 = [xi['input_ids'] + [0]*(maxlen - len(xi['input_ids'])) for xi in x12_dic]
            #对mask进行padding
            x12_mask = [xi['attention_mask'] + [0]*(maxlen - len(xi['attention_mask'])) for xi in x12_dic]
            return torch.LongTensor(x12), \
                   torch.LongTensor(x12_mask),\
                   torch.LongTensor(y)


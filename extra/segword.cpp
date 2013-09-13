// Implement by my classmate Zhang
// g++ -O2  -o segword segword.cpp
// ./segword in_doc_file_name out_words_file_name
// Only support encoding of ANSI(GBK)

#include <stdint.h>
#include <cstdio>
#include <vector>
#include <string>
#include <string.h>
#include <algorithm>
#include <cmath>
#include <limits>
#include <map>
//#include <boost/assert.hpp>
#include <ext/hash_map>
#include <ext/hash_set>
using namespace std;
using namespace __gnu_cxx;

//#define DEBUG
const uint32_t LEN = 10240;
const uint32_t BUCKET_SIZE = 1024000;

const uint32_t WORD_LEN = 6 * 2;//n个汉字
const uint32_t SHORTEST_WORD_LEN = 2;
const uint32_t LEAST_FREQ = 3;

float g_entropy_thrhd = 1;

namespace __gnu_cxx {
template<> struct hash<string>
{
    size_t operator()(const string& __s) const
    { return __stl_hash_string(__s.c_str()); }
};
template<> struct hash<const string>
{
    size_t operator()(const string& __s) const
    { return __stl_hash_string(__s.c_str()); }
};
}

struct WordInfo {
    WordInfo(): freq(0) {}
    bool calc_is_keep() {
        if (calc_is_keep_left() && calc_is_keep_right()) {
            return true;
        }
        return false;
    }
    bool calc_is_keep_left(){
        float left_entropy = calc_entropy(left_trim);
        if (left_entropy < g_entropy_thrhd) {
            return false;
        }
        return true;
    }
    bool calc_is_keep_right(){
        float right_entropy = calc_entropy(right_trim);
        if (right_entropy < g_entropy_thrhd) {
            return false;
        }
        return true;
    }
    float calc_entropy(map<string, uint32_t>& trim) {
        if (trim.size() == 0) {
            //return numeric_limits<float>::max();
            return numeric_limits<float>::min();
        }
        uint32_t trim_sum = 0;
        for (map<string, uint32_t>::iterator it = trim.begin(); it != trim.end(); ++it) {
            trim_sum += it->second;
        }
        float entropy = 0.0;
        for (map<string, uint32_t>::iterator it = trim.begin(); it != trim.end(); ++it) {
            float p = static_cast<float>(it->second) / trim_sum;
            entropy -= p * log(p);
        }
        return entropy;
    }
    uint32_t freq;
    map<string, uint32_t> left_trim;
    map<string, uint32_t> right_trim;
};

typedef __gnu_cxx::hash_map<string, WordInfo> WordInfoMap;

int gbk_char_len(const char* str)
{
    return (unsigned char)str[0] < 0x80 ? 1 : 2;
}

bool gbk_hanzi(const char* str)
{
    int char_len = gbk_char_len(str);
    if (char_len == 2 && (unsigned char)str[0] < 0xa1 || (unsigned char)str[0] > 0xa9) {
        return true;
    }
    return false;
}


int unhanzi_to_space(char* oline, const char* iline)
{
    const uint32_t line_len = strlen(iline);
    uint32_t io = 0;
    bool is_prev_hanzi = false;
    for (uint32_t ii = 0; ii < line_len;) {
        const uint32_t char_len = gbk_char_len(iline + ii);
#ifdef DEBUG
        {
            string tmp(iline + ii, iline + ii + char_len);
            fprintf(stderr, "DEBUG, phrase[%s]\n", tmp.c_str());
        }
#endif
        if (gbk_hanzi(iline + ii)) {
            memcpy(oline + io, iline + ii, char_len);
            io += char_len;
            is_prev_hanzi = true;
#ifdef DEBUG
            string tmp(iline + ii, iline + ii + char_len);
            fprintf(stderr, "DEBUG, hanzi phrase[%s]\n", tmp.c_str());
#endif
        } else {
            if (is_prev_hanzi) {
                oline[io++] = ' ';
                is_prev_hanzi = false;
            }
        }
        ii += char_len;
        //BOOST_ASSERT(ii < line_len);
        if (ii > line_len) {
			//fprintf(stderr, "WARNING, last character[%s] length wrong line[%s]\n", iline + ii - char_len, iline);
			;
        }
    }
    oline[io] = '\0';
    return 0;
}

int space_seperate_line_to_hanzi_vector(vector<string>* p_hzstr_vec, char* oline)
{
#ifdef DEBUG
    fprintf(stderr, "NOTICE, cur oline[%s]\n", oline);
#endif
    char* pch = strtok(oline, " ");
    while (pch != NULL) {
        string hzstr(pch);
#ifdef DEBUG
        fprintf(stderr, "DEBUG, cur hanzi[%s]\n", pch);
#endif
        p_hzstr_vec->push_back(hzstr);
        pch = strtok(NULL, " ");
    }
    return 0;
}

//caution: 考虑到仅仅支持gbk，又都是汉字，字符定长为2 bytes
int gen_words_freq(WordInfoMap *wordinfo_map, vector<string>& hzstr_vec)
{
    for (vector<string>::iterator it = hzstr_vec.begin(); it != hzstr_vec.end(); ++it) {
        uint32_t phrase_len = min(static_cast<uint32_t>(it->length()), WORD_LEN);
        for (uint32_t i = 2; i <= phrase_len; i += 2) {
            for (string::iterator ic = it->begin(); ic < it->end() - i + 2; ic += 2) {
                string tmp(ic, ic + i);
                WordInfoMap::iterator it_map = wordinfo_map->find(tmp);
                if (it_map == wordinfo_map->end()) {
                    WordInfo tmp_wordinfo;
                    tmp_wordinfo.freq = 1;
                    (*wordinfo_map)[tmp] = tmp_wordinfo;
                } else {
                    ++it_map->second.freq;
#ifdef DEBUG
                    fprintf(stderr, "DEBUG, word[%s], freq[%d]\n", it_map->first.c_str(), it_map->second.freq);
#endif
                }
            }
        }
    }
    return 0;
}

int gen_cad_words(hash_set<string>* cad_words_set, WordInfoMap& wordinfo_map)
{
    uint32_t total_freq = 0;
    for (WordInfoMap::iterator it = wordinfo_map.begin(); it != wordinfo_map.end(); ++it) {
        uint32_t freq = it->second.freq;
        total_freq += freq;
        //fprintf(stdout, "%s\t%d\n", it->first.c_str(), freq);
    }
    //fprintf(stdout, "%d\n", total_freq);
    for (WordInfoMap::iterator it = wordinfo_map.begin(); it != wordinfo_map.end(); ++it) {
        string& word = const_cast<string&>(it->first);
        WordInfo& wordinfo = it->second;
        if (word.length() <= SHORTEST_WORD_LEN) {
            continue;
        }
        if (wordinfo.freq < LEAST_FREQ) {
            continue;
        }
        uint32_t max_ff = 0;
        for (string::iterator ic = word.begin() + 2; ic <= word.end() - 2; ic += 2) {
            string temp_left(word.begin(), ic);
            uint32_t left_f = wordinfo_map.find(temp_left)->second.freq;

            string temp_right(ic, word.end());
            uint32_t right_f = wordinfo_map.find(temp_right)->second.freq;

            max_ff = max(left_f * right_f, max_ff);
        }
        if (static_cast<double>(total_freq) * wordinfo.freq / max_ff > 100.0) {
            cad_words_set->insert(word);
#ifdef DEBUG
            //if (cad_words_set->insert(word)) {
            //    fprintf(stderr, "FATAL, set word[%s] failed\n", word.c_str());
            //    return -1;
            //}
			fprintf(stderr, "cadword[%s], freq[%d]\n", word.c_str(), wordinfo.freq);
#endif
        }
    }
#ifdef DEBUG
    fprintf(stderr, "cad_words_size[%d]\n", cad_words_set->size());
#endif
    return 0;
}

int gen_trim_entropy(hash_set<string>& cad_words_set, WordInfoMap* wordinfo_map)
{
    for (WordInfoMap::iterator it = wordinfo_map->begin(); it != wordinfo_map->end(); ++it) {
        string& word = const_cast<string&>(it->first);
        uint32_t freq = it->second.freq;
        if (word.length() >= 3 * 2) {//三个汉字，abc，插入词bc's left trim a，插入词ab's right trim c
            string left_trim(word.begin(), word.begin() + 2);
            string right_part(word.begin() + 2, word.end());
            if (cad_words_set.find(right_part) != cad_words_set.end()) {
                WordInfoMap::iterator it_r = wordinfo_map->find(right_part);
                if (it_r == wordinfo_map->end()) {
                    fprintf(stderr, "WARNING, word[%s] in cad word, not in word_info", right_part.c_str());
                    continue;
                }
                it_r->second.left_trim[left_trim] += freq;
#ifdef DEBUG
                fprintf(stderr, "DEBUG, word[%s],left_trim[%s]\n", word.c_str(), left_trim.c_str());
#endif
            }
            string right_trim(word.end() - 2, word.end());
            string left_part(word.begin(), word.end() - 2);
            if (cad_words_set.find(left_part) != cad_words_set.end()) {
                WordInfoMap::iterator it_l = wordinfo_map->find(left_part);
                if (it_l == wordinfo_map->end()) {
                    fprintf(stderr, "WARNING, word[%s] in cad_word, not in word_info", left_part.c_str());
                    continue;
                }
                it_l->second.right_trim[right_trim] += freq;
#ifdef DEBUG
                fprintf(stderr, "DEBUG, word[%s],right_trim[%s]\n", word.c_str(), right_trim.c_str());
#endif
            }
        }
    }
    return 0;
}

int trim_entropy_filter(vector<string>* keep_words, hash_set<string>& cad_words_set, WordInfoMap& wordinfo_map)
{
    keep_words->reserve(cad_words_set.size());
    for (hash_set<string>::iterator it = cad_words_set.begin(); it != cad_words_set.end(); ++it) {
        WordInfoMap::iterator it_map = wordinfo_map.find(*it);
        if (it_map == wordinfo_map.end()) {
            fprintf(stderr, "WARNING, word[%s] in cad_word, not in word_info", it->c_str());
            continue;
        }
        if (it_map->second.calc_is_keep()) {
            keep_words->push_back(*it);
        }
    }
    return 0;
}

int dump_to_file(vector<string>& keep_words, const char* ofile_name, WordInfoMap& wordinfo_map)
{
    FILE* fd = fopen(ofile_name, "w");
    if (fd == NULL) {
        fprintf(stderr, "FATAL, open ofile[%s] failed\n", ofile_name);
        return -1;
    }
    for (vector<string>::iterator it = keep_words.begin(); it != keep_words.end(); ++it) {
        WordInfo& wordinfo = wordinfo_map.find(*it)->second;
        //fprintf(fd, "word[%s]\tfreq[%d]\tlentro[%f]\trentro[%f]\n",
        //        it->c_str(), wordinfo.freq, wordinfo.calc_entropy(wordinfo.left_trim), wordinfo.calc_entropy(wordinfo.right_trim));
        fprintf(fd, "%s\t%d\t%f\t%f\n",
                it->c_str(), wordinfo.freq, wordinfo.calc_entropy(wordinfo.left_trim), wordinfo.calc_entropy(wordinfo.right_trim));
    }
    return 0;
}

int main (int args, char* argv[])
{
    if (args != 3) {
        fprintf(stdout, "./segword in_doc_file_name out_words_file_name\n");
        return -1;
    }
    const char* in_file_name = argv[1];
    const char* out_file_name = argv[2];
    FILE* fd_in = fopen(in_file_name, "r");
    char line[LEN];
    char oline[LEN];
    vector<string> hzstr_vec;//todo reserv
    while (fgets(line, LEN, fd_in)) {
        unhanzi_to_space(oline, line);
        space_seperate_line_to_hanzi_vector(&hzstr_vec, oline);
    }
    fclose(fd_in);

    WordInfoMap wordinfo_map(BUCKET_SIZE);
    gen_words_freq(&wordinfo_map, hzstr_vec);
    hash_set<string> cad_words_set(BUCKET_SIZE / 10);
    gen_cad_words(&cad_words_set, wordinfo_map);
    gen_trim_entropy(cad_words_set, &wordinfo_map);
    vector<string> keep_words;
    trim_entropy_filter(&keep_words, cad_words_set, wordinfo_map);
    dump_to_file(keep_words, out_file_name, wordinfo_map);
    return 0;
}

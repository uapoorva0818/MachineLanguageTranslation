import collections
import csv
import itertools
from random import random
import pandas as pd

class NLP:
    def __init__(self):
        swedishOpen = open("europarl-v7.sv-en.lc.sv", "r")
        englishOpen = open("europarl-v7.sv-en.lc.en", "r")
        self.swedishWords = swedishOpen.read().split(' ')
        self.englishWords = englishOpen.read().split(' ')

        swedishOpen = open("europarl-v7.sv-en.lc.sv", 'r')
        englishOpen = open("europarl-v7.sv-en.lc.en", 'r')

        self.swedishLines = swedishOpen.readlines()
        self.englishLines = englishOpen.readlines()


        self.swedishWordCount = collections.Counter(self.swedishWords)
        self.englishWordCount = collections.Counter(self.englishWords)

        self.numberOfEnglishWords = len(self.englishWords)
        self.translationProbabilities = None


    def GetEnglishWords(self):
        return self.englishWords

    def GetMostCommonWords(self):

        print(self.swedishWordCount.most_common(15))
        print(self.englishWordCount.most_common(15))

    def GetEnglishWordProbabilty(self,word):

        return(self.englishWordCount[word] / self.numberOfEnglishWords)

    def CreateBigrams(self,words):
        bigramCount = {}
        wordCount = {}

        for i in range(len(words) - 1):
            firstWord = words[i]
            secondWord = words[i+1]
            if (firstWord,secondWord) in bigramCount:
                bigramCount[(firstWord,secondWord)] += 1
            else:
                bigramCount[(firstWord,secondWord)] = 1

            if firstWord in wordCount:
                wordCount[firstWord] += 1
            else:
                wordCount[firstWord] = 1

        return bigramCount,wordCount

    def GetBigramProb(self,bigramCount,wordCount):
        dictOfProbabilities = {}
        for key in bigramCount:
            firstWord = key[0]
            dictOfProbabilities[key] = bigramCount[key] / wordCount[firstWord]
        return dictOfProbabilities

    def GetSentenceProbability(self,sentence,bigramProbability):

        words = sentence.split()
        outputProbabilitySum = 0
        bigrams = []
        for i in range(len(words) - 1):
            bigrams.append((words[i], words[i + 1]))
        sentenceLength = 1
        for bigram in bigrams:
            sentenceLength += 1
            if bigram in bigramProbability:
                outputProbabilitySum += bigramProbability[bigram]
            else:
                # If word has not be seen in training, assign no probability
                outputProbabilitySum += 0
        sentenceProbability = outputProbabilitySum/sentenceLength
        return sentenceProbability

    def GenerateTranslationProbabilitiesAsCsv(self):

        sentencePairs = []
        for englishSentence,swedishSentence, in zip(self.englishLines,self.swedishLines):
            sentencePairs.append((englishSentence, swedishSentence))
        iterations = 100

        translationProbability = {}
        #For saving translation probabilities of european:
        q = csv.writer(open("eroupeanTranslation.csv", "w", newline=''))

        for i in range(iterations):
            print(i)
            cWordPairs = {}
            cWords = {}

            for sentencePair in sentencePairs:

                for sWord in sentencePair[1].split(' '):

                    denominator = {}
                    denominator[sWord] = 0
                    eWords = sentencePair[0].split(' ')
                    eWords.append(None)
                    for eWord in eWords:

                        if (sWord, eWord) in translationProbability:
                            denominator[sWord] += translationProbability[(sWord, eWord)]
                        else:
                            denominator[sWord] += random()

                    eWords = sentencePair[0].split(' ')
                    eWords.append(None)

                    for eWord in eWords:

                        if (sWord, eWord) in translationProbability:

                            numerator = translationProbability[(sWord, eWord)]
                        else:
                            numerator = random()

                        allignmentProbabitly = numerator / denominator[sWord]
                        if eWord in cWords:
                            cWords[eWord] += allignmentProbabitly
                        else:
                            cWords[eWord] = allignmentProbabitly

                        if (eWord, sWord) in cWordPairs:
                            cWordPairs[(eWord, sWord)] += allignmentProbabitly
                        else:
                            cWordPairs[(eWord, sWord)] = allignmentProbabitly

            for sentencePair in sentencePairs:

                for sWord in sentencePair[1].split(' '):
                    eWords = sentencePair[0].split(' ')
                    eWords.append(None)
                    for eWord in eWords:
                        translationProbability[(sWord, eWord)] = cWordPairs[(eWord, sWord)] / cWords[eWord]


        w = csv.writer(open("translationProbability.csv", "w",newline=''))
        for key, val in translationProbability.items():
            if val > 0.001:


                numberOfKeyOnes = max(1,self.englishWordCount[key[1]])
                numberOfKeyZeros = max(1,self.swedishWordCount[key[0]])


                ratioOne = numberOfKeyOnes/numberOfKeyZeros
                ratioTwo = 1/ratioOne

                commonnessRatio = min(ratioOne,ratioTwo)

                w.writerow([key[0],key[1], val*commonnessRatio])


        for key, val in translationProbability.items():
            if key[1] == 'european':
                q.writerow([key[0], key[1], val])


    def GetMostLikelyTranslations(self,swedishWord):

        translations = pd.read_csv("translationProbability.csv",names=['swedish','english','prob'])
        translations = translations.loc[translations['swedish'] == swedishWord]
        translations = translations.sort_values(by=['prob'],ascending=False)


        if translations.empty:
            print('[Can not translate: ' + str(swedishWord) + ' translating rest of sentence:]')
            return '[]'
        elif len(translations.index) > 2 and translations.head(3)['prob'].values[1] > 0.1:
            return translations.head(2)['english'].values
        else:
            return translations.head(1)['english'].values

    def FindBestWordOrder(self,englishSentence,bigramProbabilities):
        bestSoFar = self.GetSentenceProbability(englishSentence,bigramProbabilities)
        englishWords = englishSentence.split(' ')
        i = 0
        while i in range(len(englishWords)-1):

            englishWords[i], englishWords[i+1] = englishWords[i+1], englishWords[i]
            englishSentence = ' '.join(englishWords)
            if self.GetSentenceProbability(englishSentence,bigramProbabilities) > bestSoFar*2:
                i += 1
            else:
                englishWords[i], englishWords[i + 1] = englishWords[i + 1], englishWords[i]
            i+=1

        englishSentence = ' '.join(englishWords)
        return englishSentence

    def GetMostLikelyWords(self,wordOptions,bigramProbabilities):

        mostLikelyWords = ''
        highestProbabilty = 0
        for possibleSentence in [' '.join(s) for s in itertools.product(*wordOptions)]:
            prob = self.GetSentenceProbability(possibleSentence,bigramProbabilities)
            if prob > highestProbabilty:
                highestProbabilty = prob
                mostLikelyWords = possibleSentence
        return mostLikelyWords.split(' ')

    def TranslateSwedishSentence(self,swedishSentence,bigramProbabilities):
        swedishWords = swedishSentence.split(' ')
        englishWordOptions = []

        for word in swedishWords:
            englishWordOptions.append(self.GetMostLikelyTranslations(word))

        englishWords = self.GetMostLikelyWords(englishWordOptions,bigramProbabilities)
        englishSentence = ' '.join(englishWords)
        englishSentence = self.FindBestWordOrder(englishSentence,bigramProbabilities)

        return englishSentence



NLP = NLP()
print('Most common words in english & swedish files')
NLP.GetMostCommonWords()

print('Probabilty of the words zebra and speaker occuring in file')
print(NLP.GetEnglishWordProbabilty('zebra'))
print(NLP.GetEnglishWordProbabilty('speaker'))


englishBigramCount,englishWordCount = NLP.CreateBigrams(NLP.GetEnglishWords())
englishBigramProbabilities = NLP.GetBigramProb(englishBigramCount,englishWordCount)

sentence = 'i accept that but with reservations'
print('Probability of sentence: ' + sentence)
print("{:.2%}".format(NLP.GetSentenceProbability(sentence,englishBigramProbabilities)))

sentence = 'i reservations accept but that with'
print('Probability of sentence: ' + sentence)
print("{:.2%}".format(NLP.GetSentenceProbability(sentence,englishBigramProbabilities)))

#NLP.GenerateTranslationProbabilitiesAsCsv()

print(NLP.TranslateSwedishSentence('ni är',englishBigramProbabilities))
print(NLP.TranslateSwedishSentence('flera bombexplosioner har inträffat i tyskland påstår brittiska regeringen',englishBigramProbabilities))
print(NLP.TranslateSwedishSentence('jag kan tala tyska',englishBigramProbabilities))


translations = pd.read_csv("eroupeanTranslation.csv", names=['swedish','english', 'prob'])
translations = translations.sort_values(by=['prob'], ascending=False)
print(translations.head(11))
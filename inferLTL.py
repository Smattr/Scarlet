from booleanSetCover import BooleanSetCover
from isubTraces import iSubTrace
from formulaTree import Formula
from sample import Sample
import time
import heapq as hq
import logging
import csv
'''
Possible clean-ups:
- upperbound can be class variable in iSubTrace 
- 

'''
#alphabet=[]

'''
X-subsequence 	X^{i_1 -1} a_1 AND (X^{i_2 - 1} a_2 AND (...))
F-subsequence = subsequence	F a_1 AND (F a_2 AND (...))
indexed subsequence:	mix of both
'''

#BY DEFAULT p,q,r... alphabet
def isubTrace2Formula(isubtrace: tuple):

	# add formula calculation in isubTrace2FaXttern
	#print(isubtrace)

	if isubtrace[0]!='!':
		first_digit = int(isubtrace[0].strip('>'))
		first_atom = isubtrace[1]#('>0',('+0','-1'), ...)
		if first_atom[0][0] == '+': 
			form_atom = Formula(alphabet[int(first_atom[0][1:])])
		else:
			form_atom = Formula(['!', Formula(alphabet[int(first_atom[0][1:])])])

		for i in first_atom[1:]:
			if i[0] == '+':
				form_atom = Formula(['&', form_atom, Formula(alphabet[int(i[1:])])])
			else:
				form_atom = Formula(['&', form_atom, Formula(['!', Formula(alphabet[int(i[1:])])])])
		
		if len(isubtrace)>2:
			next_formula = Formula(['&', form_atom, isubTrace2Formula(isubtrace[2:])])
		else:
			next_formula = form_atom
		for i in range(first_digit):
			next_formula = Formula(['X', next_formula])
		if isubtrace[0][0]=='>':
			next_formula = Formula(['F', next_formula])
	
	else:
		first_digit = int(isubtrace[1].strip('>'))
		first_atom = isubtrace[2]#('>0',('+0','-1'), ...)
		if first_atom[0][0] == '-': 
			form_atom = Formula(alphabet[int(first_atom[0][1:])])
		else:
			form_atom = Formula(['!', Formula(alphabet[int(first_atom[0][1:])])])

		for i in first_atom[1:]:
			if i[0] == '-':
				form_atom = Formula(['|', form_atom, Formula(alphabet[int(i[1:])])])
			else:
				form_atom = Formula(['|', form_atom, Formula(['!', Formula(alphabet[int(i[1:])])])])
		
		if len(isubtrace)>3:
			next_formula = Formula(['|', form_atom, isubTrace2Formula(('!',)+isubtrace[3:])])
		else:
			next_formula = form_atom
		
		if isubtrace[1][0]=='>':
			next_formula = Formula(['G', next_formula])

		for i in range(first_digit):
			#next_formula = Formula(['|', Formula(['X', next_formula]), Formula('L')])
			next_formula = Formula(['X', next_formula])

	return next_formula

def iteration_seq(max_len, max_width):
	'''
	returns a list of pairs (l,w) specifying the order in which we try
	patterns of length l and width w

	Example:
	TO DO 
	'''
	seq=[]
	min_val = max_len+max_width
	curr_sum=2
	while curr_sum<min_val:
		for j in range(1,curr_sum):
			if curr_sum-j<= max_len and j<=max_width:
				seq.append((curr_sum-j,j))
		curr_sum=curr_sum+1
	return seq

#csvname is only temporary:
def inferLTL(sample, csvname, operators=['F', 'G', 'X', '!', '&', '|'], last=False):
	time_counter = time.time()

	# while():
	# 	alphabet += best5formulas from the heap
	# alphabet = [a,b,c]
	# alphabet = [phi1,phi2,a,b,c]


	# set of methods for indexed subsequences
	s = iSubTrace(sample, operators,last)
	
	global alphabet
	alphabet=sample.alphabet

	if last:
		alphabet.append('L')
	
	upper_bound = 4*s.max_positive_length
	# set of methods for Boolean set cover
	setcover = BooleanSetCover(sample, operators)
	max_len = s.max_positive_length
	if sample.is_words:
		if last:
			# not quite because we don't want p and q
			max_width = 2
		else:
			max_width = 1
	else:
		if last:
			max_width = len(sample.positive[0].vector[0])+1
		else:
			max_width = len(sample.positive[0].vector[0])
	# sequence of pairs (l,w) representing lengths and widths
	seq = iteration_seq(max_len, max_width)
	positive_set = {i for i in range(len(sample.positive))}
	negative_set = {i for i in range(len(sample.negative))}
	full_set = (positive_set, negative_set)
	covering_formula = None
	setcover_time = 0
	#print(max_len, max_width,seq)
	for (length, width) in seq:
		logging.info("-------------Finding from length %d and width %d isubtraces-------------"%(length,width))
		time1 = time.time()
		if width>upper_bound:
			break

		if 3*length + width -3 >= upper_bound:
			continue

		# phi = 
		# boolean combinations of
		# indexed subsequences

		# adding new letter would capture this:
		# F (G p and G q)

		# Open question: 
		# LTL over finite traces minus Until = 
		# LTL(F, X, AND, OR, Last) cup LTL(G, X, AND, OR, Last) 

		# letter = (X^10 (a and F b) AND sub2)
		# letter2 = X^10 (a and F b) OR sub3

		cover_set = s.coverSet(length, width, upper_bound)
		if cover_set=={}:
			continue

		for isubtrace in cover_set.keys():

			pos_friend_set = cover_set[isubtrace][0]
			neg_friend_set = cover_set[isubtrace][1]


			if neg_friend_set == negative_set:
				continue

			formula = isubTrace2Formula(isubtrace)
			#Is the formula equivalent to some existing formula? if yes, ignore it.
			if isubtrace[0]!='!':
				formula.size = s.len_isubtrace[(isubtrace,False)]
			else:
				formula.size = s.len_isubtrace[(isubtrace[1:], True)]
			setcover.formula_dict[formula] = (pos_friend_set, neg_friend_set)
			#score can be weighted by formula size 
			setcover.score[formula] = (len(pos_friend_set) - len(neg_friend_set) + len(negative_set))
			#print(isubtrace, formula, len(pos_friend_set),len(neg_friend_set),len(negative_set), setcover.score[formula] )
			setcover.cover_size[formula]  = len(pos_friend_set) - len(neg_friend_set) + len(negative_set)
			hq.heappush(setcover.heap, (-setcover.score[formula], formula))

			
		t0=time.time()
		current_covering_formula, upper_bound = setcover.find(upper_bound)
		t1=time.time()
		setcover_time+=t1-t0


		if current_covering_formula != None and covering_formula != current_covering_formula:
			#upper_bound = covering_formula.treeSize()
			covering_formula = current_covering_formula
			logging.info("Already found: %s"%covering_formula)
			logging.debug("Current formula upper bound %d"%upper_bound)
			
			if csvname != None:
				time_elapsed = round(time.time() - time_counter,3)
				with open(csvname, 'w') as csvfile:
					writer = csv.writer(csvfile)
					writer.writerow([time_elapsed, covering_formula.size, covering_formula.prettyPrint(), None])
			
		logging.debug('########Time taken for iteration %.3f########'%(time.time()-time1))

	logging.debug("Setcover Time %.3f"%setcover_time)
		
	if covering_formula == None:
		logging.warning("No formula found")
	else:
		time_elapsed = time.time() - time_counter
		logging.warning("Final formula found %s"%covering_formula.prettyPrint())
		logging.warning("Time taken is: "+ str(round(time_elapsed,3))+ " secs") 

	ver = sample.isFormulaConsistent(covering_formula)
	if not ver:
		logging.error("Inferred formula is inconsistent, please report to the authors")
		return
	else:
		logging.debug("Inferred formula is correct")

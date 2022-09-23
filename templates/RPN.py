def rpn(tokens):
	stack = []
	for ele in tokens:
		print(ele, stack)
		if (ele[0] == "-" and len(ele) > 0) or ele.isnumeric():
			stack.append(int(ele))

		else:
			val1, val2 = stack.pop(), stack.pop()
			if ele == "+":
				stack.append(val1+val2)
			elif ele == "-":
				stack.append(val2-val1)
			elif ele == "*":
				stack.append(val1*val2)
			else:
				if abs(val1) > abs(val2):
					stack.append(0)
				else:
					stack.append(val2//val1)
	return stack.pop()

print(rpn(["10","6","9","3","+","-11","*","/","*","17","+","5","+"]))
print(rpn(["2","1","+","3","*"]))
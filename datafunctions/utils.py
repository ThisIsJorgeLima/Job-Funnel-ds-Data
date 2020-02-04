"""
Common utility functions.
"""

import re


def descendants(cls: type) -> list:
	"""
	Return a list of all descendant classes of a class

	Arguments:
		cls (type): Class from which to identify descendants
	Returns:
		subclasses (list): List of all descendant classes
	"""

	subclasses = cls.__subclasses__()
	for subclass in subclasses:
		subclasses.extend(descendants(subclass))

	return(subclasses)


def titlecase(s: str) -> str:
	"""
	Titlecases a string in a stricter manner.
		Does not fail on symbols and apostrophes.

	Args:
		s (str): string to titlecase

	Returns:
		str: titlecased string
	"""

	return (
		re.sub(
			r"^[A-Za-z]+",
			lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(),
			re.sub(
				r"(?<=[\n 	])[A-Za-z]+",
				lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(),
				s
			)
		)
	)

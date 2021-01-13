import pandas as pd
import rating.models
import data.models
import alignment.models
from nltk import agreement
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import user_passes_test
# from django.forms.models import model_to_dict


def export_rating():  #output_path
	# using same export format as proposed in Alva-Manchego etal. (2020) https://www.aclweb.org/anthology/2020.acl-main.424.pdf
	result_frame = pd.DataFrame(
		columns=["original", "simplification", "original_sentence_id", "aspect", "worker_id", "rating"])
	i = 0
	non_aspect_fields = ['pair', 'id', 'certainty', 'comment', 'created_at', 'updated_at', 'finished_at', 'duration',
						 'rater']
	aspects = [model_field for model_field in alignment.models.Rating._meta.get_fields() if
			   model_field.name not in non_aspect_fields]
	for pair in alignment.models.Pair.objects.all():
		for pair_rating in pair.rating.all():
			original = " ".join(pair.complex_elements.values_list("original_content", flat=True))
			simplification = " ".join(pair.simple_elements.values_list("original_content", flat=True))
			original_sentence_id = pair.pair_identifier
			worker_id = pair_rating.rater.id
			for field in aspects:
				result_frame.loc[i] = [original, simplification, original_sentence_id, field.name, worker_id, field.value_from_object(pair_rating)]
				i += 1
			i += 1
		i += 1
	return result_frame


def export_transformation():
	result_frame = pd.DataFrame(
		columns=["original", "simplification", "original_sentence_id", "transformation_level", "transformation",
				 "subtransformation", "old text", "new_text", "worker_id"])
	i = 0
	for pair in alignment.models.Pair.objects.all():
		for pair_transformations in pair.transformation_of_pair.all():
			original = " ".join(pair.complex_elements.values_list("original_content", flat=True))
			simplification = " ".join(pair.simple_elements.values_list("original_content", flat=True))
			original_sentence_id = pair.pair_identifier
			worker_id = pair_transformations.rater.id
			print(pair_transformations)
			old_text = ' '.join(pair_transformations.complex_token.values_list("text", flat=True))
			new_text = ' '.join(pair_transformations.simple_token.values_list("text", flat=True))
			result_frame.loc[i] = [original, simplification, original_sentence_id,
								   pair_transformations.transformation_level,
								   pair_transformations.transformation,
								   pair_transformations.sub_transformation,
								   old_text, new_text, worker_id]
			i += 1
		i += 1
	return result_frame


def export_alignment():
	"""create one simple and complex file per annotator. The simple and the complex file contains all alignments no matter their domain or corpus."""
	# todo: add sources and copyright information to texts!
	corpus_name = "DEplain"
	for rater in set(data.models.DocumentPair.objects.values_list("annotator", flat=True)):
		print(rater)
		rater_str = ".rater." + str(rater)
		file_name_complex = corpus_name + ".orig" + rater_str
		file_name_simple = corpus_name + ".simp" + rater_str
		output_text_simple = ""
		output_text_complex = ""
		for document_pair in data.models.DocumentPair.objects.filter(annotator=rater):
			for alignment in document_pair.sentence_alignment_pair.filter(annotator=rater):
				output_text_simple += " ".join(alignment.simple_elements.values_list("original_content", flat=True)) + "\n"
				output_text_complex += " ".join(alignment.complex_elements.values_list("original_content", flat=True)) + "\n"
		with open(file_name_complex, "w") as f:
			f.write(output_text_complex)
		with open(file_name_simple, "w") as f:
			f.write(output_text_simple)
	return 1

def get_inter_annotator_agreement(aspect):
	# extract all raters
	list_rater_ids = rating.models.Rating.objects.order_by().values_list('rater_id', flat=True).distinct()
	list_pair_identifier = alignment.models.Pair.objects.order_by().values_list('pair_identifier', flat=True).distinct()

	output_list = [list(list_pair_identifier)]
	for id_rater in list_rater_ids:
		inner_list = list()
	# print("number ids", len(Pair.objects.order_by().values_list('pair_identifier', flat=True).distinct()))
		for pair_id in list_pair_identifier:
			relevant_object = alignment.models.Pair.objects.filter(annotator_id=id_rater, pair_identifier=pair_id)
			if relevant_object:
				inner_list.append(getattr(relevant_object[0].rating, aspect))
			else:
				inner_list.append(None)
		output_list.append(inner_list)
	# outputlist: values only for meaning_preservation. first row object identifiers of pairs, row per annotator. values are ratings per record with missing values
	output = list()
	for n, coder in enumerate(output_list):
		for i in range(len(coder)):
			output.append([n + 1, i, coder[i]])
	ratingtask = agreement.AnnotationTask(data=output)
	# following the example of https://learnaitech.com/how-to-compute-inter-rater-reliablity-metrics-cohens-kappa-fleisss-kappa-cronbach-alpha-kripndorff-alpha-scotts-pi-inter-class-correlation-in-python/
	return ratingtask.alpha()


@user_passes_test(lambda u: u.is_superuser)
def export(request):
	if request.method == "POST":
		if "export_rating" in request.POST:
			output_frame = export_rating()
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="human_ratings_ts.csv"'
			output_frame.to_csv(path_or_buf=response)
			return response
		elif "export_alignment" in request.POST:
			# todo: export as zip file
			output_frame = export_alignment()
			# response = HttpResponse(content_type='text/csv')
			# response['Content-Disposition'] = 'attachment; filename="human_ratings_ts.csv"'
			# output_frame.to_csv(path_or_buf=response)
			# return response
		elif "export_transformation" in request.POST:
			output_frame = export_transformation()
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="human_ratings_ts.csv"'
			output_frame.to_csv(path_or_buf=response)
			return response
		elif "get_iaa" in request.POST:
			iaa_meaning = get_inter_annotator_agreement("meaning_preservation")
			iaa_simplicity = get_inter_annotator_agreement("simplicity")
			iaa_grammaticality = get_inter_annotator_agreement("grammaticality")
			return render(request, 'evaluation/iaa.html', {"iaa_meaning": iaa_meaning, "iaa_simplicity": iaa_simplicity,
														   "iaa_grammaticality": iaa_grammaticality})
	return render(request, 'evaluation/home.html', {})


# @user_passes_test(lambda u: u.is_superuser)
# def iaa(request):
# 	"""
# 	show inter annotator agreement
# 	"""
# 	return render(request, 'evaluation/iaa.html')





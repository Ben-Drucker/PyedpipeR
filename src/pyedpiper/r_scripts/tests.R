devtools::install("~/Desktop/uniprot.tools.R/")

uniprot.tools.R::write_fasta()

uniprot.tools.R::write_fasta(seqs = list("ACDEF"), seq_descriptions = list("Seq1"), outfile = "/Users/druc594/Desktop/test_outfile.fasta")

a2pi <- uniprot.tools.R::accession_to_prot_info(accessions = c("P12345", "P12346"), knowledge_base = "uniprotkb", columns = c("accession", "reviewed", "protein_name", "gene_names", "organism_name"), num_simultaneous_requests = 100L)

uniprot.tools.R
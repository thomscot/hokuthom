import os
import smtplib
import time
import logging

from app import app
from datetime import date, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template, request, redirect, jsonify
from smtplib import SMTPAuthenticationError, SMTPException
from typing import Optional


IN_JAPAN_SINCE = date(2012, 3, 28)     
WRITING_SINCE = date(2021, 1, 7)
BIRTHDATE = date(1984, 3, 12)

def full_years_since(start_date: date, today: Optional[date] = None) -> int:
    today = today or date.today()
    years = today.year - start_date.year
    if (today.month, today.day) < (start_date.month, start_date.day):
        years -= 1
    return max(0, years)


def calc_age(birthdate: date, today: Optional[date] = None) -> int:
    today = today or date.today()
    return today.year - birthdate.year - (
        (today.month, today.day) < (birthdate.month, birthdate.day)
    )

@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


def lang_from_host(default="it") -> str:
    host = (request.host or "").lower().split(":")[0]
    if host in ("tomscotti.com", "www.tomscotti.com"):
        return "en"
    return default

@app.before_request
def before_request():
    """
    1) Canonical www
    2) tomscotti landing: /  -> /en  (stays on su tomscotti.com)
    3) Force https (only non-dev)
    """

    host = (request.host or "").lower().split(":")[0]
    path = request.path or "/"
    full_path = request.full_path or path  # include querystring se presente

    # --- 1) Canonical www ---
    if host == "tommasoscotti.com":
        return redirect("https://www.tommasoscotti.com" + full_path, code=301)

    if host == "tomscotti.com":
        return redirect("https://www.tomscotti.com" + full_path, code=301)

    # --- 2) Landing EN on tomscotti only if you are on / (or /index) ---
    # (so /jp stays /jp and doesn't force EN)
    if host == "www.tomscotti.com" and path in ("/", "/index"):
        return redirect("https://www.tomscotti.com/en", code=302)

    # --- 3) Force HTTPS in prod ---
    if app.env != "development":
        proto = request.headers.get("X-Forwarded-Proto", request.scheme)
        if proto != "https":
            return redirect(request.url.replace("http://", "https://", 1), code=301)


def get_translations(lang: str) -> dict:
    """
    Minimal i18n via dict. Italian is default.
    """
    lang = (lang or "it").lower()
    if lang not in ("it", "en", "jp"):
        lang = "it"

    T = {
        "it": {
            "html_lang": "it",
            "meta_description": "Scrittore italiano in Giappone. Autore di romanzi ambientati nel Giappone contemporaneo. Una traiettoria non lineare tra ricerca scientifica, tecnologia e cultura.",
            "site_name": "Tommaso Scotti",
            "header_motto": "斗 Scrittore 武",

            "nav_home": "Home",
            "nav_about": "Chi sono",
            "nav_cv": "CV",
            "nav_writing": "Scrittura",
            "nav_photography": "Fotografia",
            "nav_cultural": "Attività culturali",
            "nav_contact": "Contatti",

            "about_info_title": "Informazioni",
            "about_info_subtitle": "In due parole... ",
            "about_headline": "Scrittore italiano in Giappone",
            "about_tagline": "Una traiettoria non lineare tra ricerca scientifica, tecnologia e cultura.",
            "label_birthdate": "Data di nascita:",
            "value_birthdate": "12 Marzo 1984",
            "label_website": "Sito web:",
            "label_age": "Età:",
            "label_education": "Educazione:",
            "value_education": "Dottorato (matematica)",

            "short_story_label": "LA STORIA BREVE",
            "short_story_paragraph": (
                "Sono nato a Roma ma vivo e lavoro in Giappone dal 2012. Ho conseguito un dottorato in matematica applicata a Tokyo nel 2015, "
                "a seguito del quale ho iniziato a lavorare nell'ambiente delle tecnologie finanziarie e pubblicitarie. Mi piace anche scrivere, "
                "e nel 2021 ho pubblicato il mio primo romanzo <em>L'Ombrello dell'Imperatore</em> (Longanesi). "
                "Suono il pianoforte fin da bambino, e pratico arti marziali dalla fine degli anni 90. Nel tempo libero mi dedico alla calligrafia, "
                "giro in moto, scrivo, leggo, programmo, faccio foto e probabilmente ho dimenticato qualcosa."
            ),

            "long_story_paragraph": (
                "Sono nato e cresciuto a Roma, città che ho abitato per i primi vent’anni della mia vita, oscillando tra una precoce passione per la musica e lo sport e una costante attenzione allo studio, accuratamente sorvegliata in ambito familiare."
                "</br></br>"
                "È stato però durante l’estate del 2007, visitando un amico in Erasmus in Spagna, che ho scoperto come l’espressione “studio all’estero” possa talvolta avere contorni sorprendentemente elastici. Avendo quasi concluso una laurea specialistica in matematica, decisi che avrei voluto sperimentare anch’io quella forma di “studio”."
                "</br></br>"
                "La Spagna, tuttavia, non mi sembrava sufficientemente distante – almeno in senso caratteriale. Scelsi quindi la Finlandia, e nel gennaio del 2008 mi trasferii per un semestre all’Università di Oulu, a pochi chilometri dal Circolo Polare Artico. Fu un’esperienza formativa sotto molti aspetti: non solo per l’approfondimento accademico, ma anche perché imparai cosa significhi vivere in un contesto radicalmente diverso, confrontarsi con nuove lingue e nuove abitudini, e sviluppare una prima, concreta autonomia personale. La Finlandia rappresentò un primo passo, ma non certo l’ultimo."
                "</br></br>"
                "Conclusa la laurea nel 2009, decisi di prendermi una pausa dagli studi per seguire un’altra mia passione di lunga data: le arti marziali. Con oltre dieci anni di pratica alle spalle e una conoscenza di base del cinese, mi trasferii a Pechino. L’impatto fu tutt’altro che semplice: lo shock culturale fu notevole e i primi mesi richiesero una buona dose di adattamento e perseveranza. Superata la fase iniziale, tuttavia, la Cina si rivelò un’esperienza straordinaria, fatta di incontri, musica, pratica marziale e contatti con ambienti culturali molto diversi tra loro, che contribuirono in modo decisivo ad ampliare il mio sguardo sul mondo."
                "</br></br>"
                "Fu proprio durante il soggiorno in Cina che visitai per la prima volta il Giappone. Bastarono pochi giorni per capire che quel Paese avrebbe avuto un ruolo centrale nel mio futuro. Nel 2010 mi trasferii a Tokyo con l’idea di fermarmi più a lungo, pur senza parlare giapponese e senza una reale esperienza professionale. L’esito fu, prevedibilmente, incerto: dopo alcuni mesi dovetti rientrare in Italia. L’idea di rinunciare, però, non prese mai realmente forma. Decisi quindi di ripercorrere la via accademica e, dopo un lungo periodo di candidature e procedure, nel 2012 ottenni una borsa di studio che mi permise di trasferirmi definitivamente a Tokyo, dove vivo tuttora."
                "</br></br>"
                "Nel 2015 ho conseguito un dottorato in matematica applicata, svolgendo attività di ricerca nel campo delle equazioni di reazione-diffusione. Al termine del percorso accademico ho intrapreso una carriera professionale nel settore delle tecnologie finanziarie e, successivamente, in quello delle tecnologie pubblicitarie, lavorando in contesti internazionali e altamente interdisciplinari. Questo percorso mi ha portato gradualmente dalla matematica teorica alla programmazione e all’analisi dei dati, consentendomi di sviluppare competenze organizzative, progettuali e di coordinamento in ambienti complessi."
                "</br></br>"
                "Parallelamente, ho sempre coltivato un impegno costante nelle arti e nella cultura. Suono il pianoforte fin dall’infanzia, pratico arti marziali dalla fine degli anni Novanta e mi dedico da anni allo studio e alla pratica della calligrafia giapponese (shodō), come forma di approfondimento linguistico ed estetico della cultura nipponica. Nel 2021 ho pubblicato il mio primo romanzo, L’ombrello dell’Imperatore (Longanesi), cui sono seguite altre opere narrative ambientate in Giappone. Attraverso la scrittura svolgo un’attività di divulgazione culturale rivolta al pubblico italiano, con l’intento di raccontare il Giappone contemporaneo nelle sue sfumature, lontano da semplificazioni e stereotipi."
                "</br></br>"
                "Guardando a ritroso, il mio percorso si è sviluppato lungo una traiettoria non lineare, ma coerente: dalla formazione scientifica alla produzione culturale, passando per una lunga esperienza di vita e lavoro in Giappone. Vivere stabilmente nel Paese dal 2012 mi ha permesso di comprenderne dall’interno i codici culturali, le istituzioni e le dinamiche sociali, costruendo nel tempo un rapporto profondo e quotidiano con il contesto giapponese. Ritengo che questa combinazione di esperienza accademica, professionale e culturale possa costituire una base solida per contribuire, con consapevolezza e spirito di servizio, alla promozione della cultura italiana e al rafforzamento del dialogo culturale tra Italia e Giappone."
            ),

            "read_more": "LA STORIA LUNGA...",
            "read_less": "NASCONDI",
            "count_years_in_japan_label": "Anni in Giappone",
            "count_cultural_years_label": "Anni di attività culturale",
            "count_novels_value": "4",
            "count_novels_label": "Romanzi",
            "count_papers_value": "2",
            "count_papers_label": "Articoli scientifici",

            "writing_title": "Scrittura",
            "writing_subtitle": "I miei libri",
            "book1_url": "https://www.longanesi.it/libri/tommaso-scotti-lombrello-dellimperatore-9788830456464/",
            "book1_desc": "Un uomo viene trovato morto a Kabukichō. L’arma del delitto è tanto banale quanto inusuale: un ombrello di plastica. Quando su di esso emerge un’impronta digitale insospettabile, però, l’ispettore mezzosangue Takeshi James Nishida si trova di fronte a un caso impossibile. Un noir che intreccia indagine e società giapponese contemporanea.",
            "book2_url": "https://www.illibraio.it/libri/tommaso-scotti-le-due-morti-del-signor-mihara-9788830459168/",
            "book2_desc": "Takaji Mihara, uomo d’affari in pensione, viene trovato morto nella propria casa. L’ispettore Nishida si trova a indagare su un omicidio che sembra sfidare ogni logica investigativa, in un noir che esplora le ombre nascoste delle vite ordinarie e dei segreti sociali giapponesi. ",
            "book3_url": "https://www.longanesi.it/libri/tommaso-scotti-i-diavoli-di-tokyo-ovest-9788830460836/",
            "book3_desc": "Al dipartimento di polizia di Tokyo c'è tensione. In un piccolo parco è stato rinvenuto il cadavere di un uomo con in tasca il biglietto da visita dell’ispettore Nishida. La ricerca della verità porta Nishida ad addentrarsi nelle strade di Tokyo e nei quartieri dove si muovono i bōsōzoku, le gang di motociclisti, e a confrontarsi con un mistero personale e sociale.",
            "book4_url": "https://www.illibraio.it/libri/tommaso-scotti-il-segreto-del-vecchio-signor-nakamura-9788830462144/",
            "book4_desc": "Tokyo, 2018: un ex ispettore è chiamato a confrontarsi con il cinquantesimo anniversario di una delle indagini più celebri del Paese, il furto dei trecento milioni di yen del 1968. Tra passato e presente, il romanzo intreccia memoria, rimpianto e la tensione di un crimine senza vittime apparenti, offrendo un affresco profondo e umano del Giappone.",

            "cultural_title": "Attività culturali",
            "cultural_subtitle": "Scrittura, divulgazione e impegno culturale",
            "cultural_box1_title": "Produzione letteraria",
            "cultural_box1_text": (
                "Autore di romanzi di narrativa ambientati nel Giappone contemporaneo e pubblicati "
                "da un importante editore italiano. Attraverso la scrittura affronto temi sociali, culturali "
                "e storici della società giapponese contemporanea."
            ),
            "cultural_box2_title": "Divulgazione culturale",
            "cultural_box2_text": (
                "Attività continuativa di divulgazione rivolta al pubblico italiano, finalizzata a raccontare "
                "il Giappone al di là di stereotipi e semplificazioni, attraverso scrittura, incontri pubblici, social media "
                "e attività editoriali."
            ),
            "cultural_box3_title": "Pratiche artistiche",
            "cultural_box3_text": (
                "Impegno continuativo in ambiti artistici e disciplinari come strumenti di comprensione "
                "culturale: arti marziali (con particolare riferimento al kendō in Giappone), calligrafia "
                "giapponese (shodō, membro dell’associazione Shodan-in dal 2017) e pianoforte, che studio e "
                "suono da oltre trent’anni."
            ),
            "cultural_box4_title": "Esperienza interculturale",
            "cultural_box4_text": (
                "Oltre dieci anni di vita e lavoro in Giappone, maturati in contesti professionali e culturali "
                "internazionali, con un coinvolgimento quotidiano nelle dinamiche istituzionali, sociali "
                "e culturali del Paese."
            ),

            "contact_title": "Contatti",
            "contact_subtitle": "Contattami",
            "contact_address_title": "Il mio indirizzo",
            "contact_social_title": "Profili Social",

            "form_name_placeholder": "Il tuo nome",
            "form_email_placeholder": "La tua email",
            "form_subject_placeholder": "Oggetto",
            "form_message_placeholder": "Scrivi qualcosa qui",
            "form_submit": "Invia Messaggio",
            "form_sending": "Sto inviando il messaggio...",

            "form_msg_minlen4": "Inserisci almeno 4 caratteri",
            "form_msg_valid_email": "Inserisci un indirizzo email valido",
            "form_msg_subject_minlen4": "Inserisci un oggetto di almeno 4 caratteri",
            "form_msg_write_something": "Scrivi un messaggio",

            "conference_title": "Elenco conferenze",
            "close": "Chiudi",

            "conf_1_title": "Joint seminar between young mathematicians and the industry",
            "conf_1_place": "Tokyo University, Tokyo, Japan",
            "conf_1_date": "Ottobre 2014",
            "conf_2_title": "The 5th Japan-Taiwan workshop for young scholars in applied mathematics",
            "conf_2_place": "National Tsing Hua University, Hsinchu, Taiwan",
            "conf_2_date": "Febbraio 2014",
            "conf_3_title": "Japanese-Hungarian Conference on applied mathematics and nonlinear dynamics",
            "conf_3_place": "Budapest University of Technology and Economics, Budapest, Hungary",
            "conf_3_date": "Dicembre 2013",
            "conf_4_title": "International conference on mathematical modeling and applications",
            "conf_4_place": "Meiji University, Tokyo, Japan",
            "conf_4_date": "Novembre 2013",
            "conf_5_title": "NIMS-KMRS PDE Conference on reaction-diffusion equations for ecology and related problems",
            "conf_5_place": "KAIST, Daejeon, South Korea",
            "conf_5_date": "Ottobre 2013",
            "conf_6_title": "Models in Population Dynamics and Ecology",
            "conf_6_place": "Osnabruck, Germany",
            "conf_6_date": "Agosto 2013",
            "conf_7_title": "N2-days ReaDiLab workshop",
            "conf_7_place": "Meiji University, Tokyo",
            "conf_7_date": "Luglio 2013",
            "conf_8_title": "MIMS Mathematical biology seminars",
            "conf_8_place": "Meiji University, Tokyo, Japan",
            "conf_8_date": "Giugno 2013",

            # Contact backend responses
            "contact_ok": "Grazie! Cercherò di risponderti il prima possibile!",
            "contact_missing": "Mancano campi obbligatori.",
            "contact_server_config": "Errore di configurazione server.",
            "contact_auth_err": "Errore di autenticazione email. Contattami via social.",
            "contact_generic_err": "Si è verificato un errore :/ Riprova più tardi o contattami tramite i social.",
        },

        "en": {
            "html_lang": "en",
            "meta_description": "Italian author based in Japan. Author of crime fiction set in contemporary Japan. A non-linear trajectory across scientific research, technology, and culture.",
            "site_name": "Tom Scotti",
            "header_motto": "斗 Author 武",

            "nav_home": "Home",
            "nav_about": "About",
            "nav_cv": "Resume",
            "nav_writing": "Writing",
            "nav_photography": "Photography",
            "nav_cultural": "Cultural activities",
            "nav_contact": "Contact",

            "about_info_title": "Info",
            "about_info_subtitle": "In a nutshell...",
            "about_headline": "Italian author in Japan",
            "about_tagline": "A non-linear trajectory across scientific research, technology, and culture.",
            "label_birthdate": "Date of birth:",
            "value_birthdate": "March 12, 1984",
            "label_website": "Website:",
            "label_age": "Age:",
            "label_education": "Education:",
            "value_education": "PhD (Mathematics)",

            "short_story_label": "THE SHORT STORY",
            "short_story_paragraph": (
                "I was born in Rome, but I have been living and working in Japan since 2012. I earned a PhD in applied mathematics in Tokyo in 2015, "
                "after which I started working in the world of financial and advertising technologies. I also like writing, and in 2021 I published my first novel "
                "<em>The Emperor’s Umbrella</em> (Longanesi). "
                "I have played the piano since childhood, and I have practiced martial arts since the late 1990s. In my free time I do calligraphy, "
                "ride my motorcycle, write, read, code, take photos—and I probably forgot something."
            ),

            "long_story_paragraph": (
                "I was born and raised in Rome, a city where I spent the first twenty years of my life, balancing an early passion for music and sports with a steady dedication to studying—carefully supervised at home."
                "</br></br>"
                "It was during the summer of 2007, while visiting a friend on Erasmus in Spain, that I realized how flexible the expression “studying abroad” can be. As I was about to complete a master’s degree in mathematics, I decided I wanted to try that kind of “study” myself."
                "</br></br>"
                "Spain, however, did not feel far enough—at least in terms of temperament. So I chose Finland, and in January 2008 I moved for a semester to the University of Oulu, a few kilometers from the Arctic Circle. It was a formative experience in many ways: not only academically, but also because I learned what it means to live in a radically different context, deal with new languages and habits, and develop real personal independence. Finland was a first step, but certainly not the last."
                "</br></br>"
                "After graduating in 2009, I took a break from academia to pursue another long-standing passion: martial arts. With over ten years of practice behind me and a basic knowledge of Chinese, I moved to Beijing. The impact was far from easy: cultural shock was significant, and the first months required a good dose of adaptation and perseverance. Once the initial phase passed, however, China became an extraordinary experience—made of encounters, music, martial practice, and contact with very different cultural environments—which decisively broadened my perspective on the world."
                "</br></br>"
                "It was during my time in China that I visited Japan for the first time. A few days were enough to understand that the country would play a central role in my future. In 2010 I moved to Tokyo with the idea of staying longer, despite not speaking Japanese and without real professional experience. The outcome was, predictably, uncertain: after a few months I had to return to Italy. But giving up never really took shape. I went back to the academic path and, after a long period of applications and procedures, in 2012 I obtained a scholarship that allowed me to move permanently to Tokyo, where I still live today."
                "</br></br>"
                "In 2015 I earned a PhD in applied mathematics, conducting research on reaction-diffusion equations. After completing my academic path, I started a professional career in financial technologies and later in advertising technologies, working in international and highly interdisciplinary contexts. This gradually led me from theoretical mathematics to programming and data analysis, allowing me to develop organizational, project, and coordination skills in complex environments."
                "</br></br>"
                "In parallel, I have always cultivated a consistent commitment to arts and culture. I have played the piano since childhood, practiced martial arts since the late 1990s, and for years I have studied and practiced Japanese calligraphy (shodō) as a linguistic and aesthetic way to deepen my understanding of Japanese culture. In 2021 I published my first novel, The Emperor’s Umbrella (Longanesi), followed by other works of fiction set in Japan. Through writing, I also engage in cultural outreach for an Italian audience, with the aim of portraying contemporary Japan in its nuances—far from simplifications and stereotypes."
                "</br></br>"
                "Looking back, my path has unfolded along a non-linear yet coherent trajectory: from scientific training to cultural production, through a long experience of living and working in Japan. Living in the country since 2012 has allowed me to understand from within its cultural codes, institutions, and social dynamics, building over time a deep and everyday relationship with the Japanese context. I believe this combination of academic, professional, and cultural experience can provide a solid foundation to contribute—responsibly and with a spirit of service—to the promotion of Italian culture and to strengthening cultural dialogue between Italy and Japan."
            ),

            "read_more": "THE LONG STORY...",
            "read_less": "READ LESS...",

            "count_years_in_japan_label": "Years in Japan",
            "count_cultural_years_label": "Years of cultural activity",
            "count_novels_value": "4",
            "count_novels_label": "Novels",
            "count_papers_value": "2",
            "count_papers_label": "Scientific papers",

            "writing_title": "Writing",
            "writing_subtitle": "My books",
            "book1_url": "https://www.maurispagnol.it/en/book/tommaso-scotti-lombrello-dellimperatore-9788830456464",
            "book1_desc": "A man is found dead in Kabukichō. The murder weapon is as banal as it is unusual: a cheap plastic umbrella. When an unexpected fingerprint is discovered on it, Inspector Takeshi James Nishida—caught between two cultures—finds himself facing an impossible case. A noir that blends investigation with a sharp portrait of contemporary Japanese society.",
            "book2_url": "https://www.maurispagnol.it/en/book/tommaso-scotti-le-due-morti-del-signor-mihara-9788830459168",
            "book2_desc": "Takaji Mihara, a retired businessman, is found dead in his own home. Inspector Nishida is drawn into an investigation that defies conventional logic, in a noir that explores the hidden shadows of ordinary lives and the unspoken tensions of Japanese society.",
            "book3_url": "https://www.maurispagnol.it/en/book/tommaso-scotti-i-diavoli-di-tokyo-ovest-9788830460836/ns",
            "book3_desc": "Tension rises within the Tokyo Metropolitan Police. The body of a man is found in a small park, carrying Inspector Nishida’s business card. As he searches for the truth, Nishida is led into the streets of western Tokyo and the world of the bōsōzoku—motorcycle gangs bound by violence and loyalty—where a personal and social mystery awaits.",
            "book4_url": "https://www.maurispagnol.it/en/book/tommaso-scotti-il-segreto-del-vecchio-signor-nakamura-9788830462144",
            "book4_desc": "Tokyo, 2018. A former inspector is forced to confront the fiftieth anniversary of one of Japan’s most infamous unresolved cases: the 1968 three-hundred-million-yen heist. Moving between past and present, the novel weaves together memory, regret, and the tension of a crime without victims, offering a deeply human portrait of Japan.",

            "cultural_title": "Cultural activities",
            "cultural_subtitle": "Writing, cultural outreach, and engagement",
            "cultural_box1_title": "Literary work",
            "cultural_box1_text": (
                "Author of fiction novels set in contemporary Japan and published by a major Italian publisher. "
                "Through writing I explore social, cultural, and historical themes of contemporary Japanese society."
            ),
            "cultural_box2_title": "Cultural outreach",
            "cultural_box2_text": (
                "Ongoing outreach activity aimed at an Italian audience, meant to describe Japan beyond stereotypes and simplifications, "
                "through writing, public events, social media, and editorial work."
            ),
            "cultural_box3_title": "Artistic practices",
            "cultural_box3_text": (
                "Ongoing commitment to artistic and disciplined practices as tools for cultural understanding: martial arts "
                "(with a focus on kendō in Japan), Japanese calligraphy (shodō; member of the Shodan-in association since 2017), "
                "and piano, which I have studied and played for over thirty years."
            ),
            "cultural_box4_title": "Intercultural experience",
            "cultural_box4_text": (
                "Over ten years of living and working in Japan, in international professional and cultural contexts, "
                "with daily involvement in the country’s institutional, social, and cultural dynamics."
            ),

            "contact_title": "Contact",
            "contact_subtitle": "Get in touch",
            "contact_address_title": "My address",
            "contact_social_title": "Social profiles",

            "form_name_placeholder": "Your name",
            "form_email_placeholder": "Your email",
            "form_subject_placeholder": "Subject",
            "form_message_placeholder": "Write something here",
            "form_submit": "Send message",
            "form_sending": "Sending your message...",

            "form_msg_minlen4": "Please enter at least 4 characters",
            "form_msg_valid_email": "Please enter a valid email",
            "form_msg_subject_minlen4": "Please enter a subject of at least 4 characters",
            "form_msg_write_something": "Please write something",

            "conference_title": "Conference list",
            "close": "Close",

            "conf_1_title": "Joint seminar between young mathematicians and the industry",
            "conf_1_place": "Tokyo University, Tokyo, Japan",
            "conf_1_date": "October 2014",
            "conf_2_title": "The 5th Japan-Taiwan workshop for young scholars in applied mathematics",
            "conf_2_place": "National Tsing Hua University, Hsinchu, Taiwan",
            "conf_2_date": "February 2014",
            "conf_3_title": "Japanese-Hungarian Conference on applied mathematics and nonlinear dynamics",
            "conf_3_place": "Budapest University of Technology and Economics, Budapest, Hungary",
            "conf_3_date": "December 2013",
            "conf_4_title": "International conference on mathematical modeling and applications",
            "conf_4_place": "Meiji University, Tokyo, Japan",
            "conf_4_date": "November 2013",
            "conf_5_title": "NIMS-KMRS PDE Conference on reaction-diffusion equations for ecology and related problems",
            "conf_5_place": "KAIST, Daejeon, South Korea",
            "conf_5_date": "October 2013",
            "conf_6_title": "Models in Population Dynamics and Ecology",
            "conf_6_place": "Osnabruck, Germany",
            "conf_6_date": "August 2013",
            "conf_7_title": "N2-days ReaDiLab workshop",
            "conf_7_place": "Meiji University, Tokyo",
            "conf_7_date": "July 2013",
            "conf_8_title": "MIMS Mathematical biology seminars",
            "conf_8_place": "Meiji University, Tokyo, Japan",
            "conf_8_date": "June 2013",

            "contact_ok": "Thank you! I will get back to you as soon as possible!",
            "contact_missing": "Missing required fields.",
            "contact_server_config": "Server configuration error.",
            "contact_auth_err": "Email auth error. Please contact me via social media.",
            "contact_generic_err": "An error occurred :/ Please try later or contact me via social media.",
        },

        "jp": {
            "html_lang": "ja",
            "meta_description": "日本在住のイタリア人作家。現代日本を舞台にした小説の著者。科学研究・テクノロジー・文化を横断する、直線ではない軌跡。",
            "site_name": "スコッティ トマソ  (<ruby>斗武<rt>トム</rt></ruby>)", #"<ruby>Scotti<rt>スコッティ</rt></ruby> <ruby> Tommaso<rt>トマソ</rt></ruby> (<ruby>斗武<rt>トム</rt></ruby>)",
            "header_motto": "作家",
            "nav_home": "ホーム",
            "nav_about": "プロフィール",
            "nav_cv": "経歴",
            "nav_writing": "著作",
            "nav_photography": "写真",
            "nav_cultural": "文化活動",
            "nav_contact": "お問い合わせ",

            "about_info_title": "情報",
            "about_info_subtitle": "ひとことで言うと…",
            "about_headline": "日本在住のイタリア人作家",
            "about_tagline": "科学研究・テクノロジー・文化を横断する、直線ではない軌跡。",
            "label_birthdate": "生年月日：",
            "value_birthdate": "1984年3月12日",
            "label_website": "ウェブサイト：",
            "label_age": "年齢：",
            "label_education": "学歴：",
            "value_education": "博士号（数学）",

            "short_story_label": "簡単な経歴",
            "short_story_paragraph": (
                "ローマ生まれですが、2012年から日本で生活・仕事をしています。2015年に東京の明治大学で応用数学の博士号を取得し、 "
                "その後はフィンテックやアドテックの領域で働いてきました。執筆も続けており、2021年に初の小説 "
                "<em>L'ombrello dell'imperatore(天皇の傘, Longanesi社)</em>を刊行しました。"
                "幼い頃からピアノを弾き、1990年代後半から武道にも取り組んでいます。"
                "余暇は書道、バイク、読書、プログラミング、写真…たぶん他にも色々あります。"
            ),

            "long_story_paragraph": (
                "私はローマで生まれ育ち、人生の最初の20年ほどをその街で過ごしました。音楽とスポーツへの早い段階からの情熱と、家庭で丁寧に見守られた学業への継続的な集中、その両方の間を行き来していました。"
                "</br></br>"
                "転機は2007年の夏、スペインに留学していた友人を訪ねた時でした。「海外で学ぶ」という言葉が、時に驚くほど柔軟な輪郭を持つことに気づいたのです。数学の修士課程をほぼ終えようとしていた私は、自分もその“学び方”を経験してみたいと思いました。"
                "</br></br>"
                "ただ、スペインは（少なくとも気質という意味では）十分に遠いとは感じませんでした。そこで選んだのがフィンランドです。2008年1月、北極圏まで数キロというオウル大学に半年間留学しました。学問的な深まりだけでなく、異なる社会で生活し、新しい言語や習慣に向き合い、具体的な自立を獲得するという点でも大きな学びでした。フィンランドは最初の一歩に過ぎませんでしたが、確かな一歩でした。"
                "</br></br>"
                "2009年に卒業した後、私は学業をいったん離れ、長年のもう一つの情熱である武道に時間を使うことにしました。10年以上の稽古経験と中国語の基礎を携え、北京へ移住します。最初の数ヶ月は強いカルチャーショックがあり、適応と粘り強さが必要でした。しかしその時期を越えると、中国での生活は出会い、音楽、武術の実践、そして多様な文化環境との接触に満ちた、非常に豊かな経験となり、世界の見え方を大きく広げてくれました。"
                "</br></br>"
                "中国滞在中、私は初めて日本を訪れました。数日で、この国が将来の中心になると直感しました。2010年、まだ日本語も十分に話せず、職務経験も乏しいまま東京へ移住します。結果は予想通り不安定で、数ヶ月後にはイタリアへ戻らざるを得ませんでした。それでも“諦める”という選択肢は現実になりませんでした。学術の道に戻り、長い応募と手続きを経て、2012年に奨学金を得て東京へ定住します。以来、現在まで日本で暮らしています。"
                "</br></br>"
                "2015年に応用数学の博士号を取得し、反応拡散方程式に関する研究に取り組みました。学術課程の後はフィンテック、続いてアドテック領域で国際的かつ学際的な環境で働き、理論数学からプログラミングとデータ分析へと活動領域を広げてきました。その過程で、複雑な現場における組織運営、企画推進、調整といった力も培われました。"
                "</br></br>"
                "同時に、芸術と文化への継続的な関わりも途切れたことはありません。幼少期からピアノを学び、1990年代後半から武道を続け、近年は日本文化を言語的・美的に掘り下げる方法として書道（書壇院に2017年より所属）にも取り組んでいます。2021年には初の小説を刊行し、その後も日本を舞台にした作品を発表してきました。執筆を通じて、ステレオタイプを避けながら、現代日本の多層的な姿をイタリアの読者へ伝える文化発信も行っています。"
                "</br></br>"
                "振り返ると、私の歩みは決して直線的なものではありませんが、一貫した流れをもつものでした。科学的な訓練を出発点とし、文化的な創作活動へと展開しながら、2012年以降は日本で生活し、働いてきました。長年にわたり日本に根を下ろして暮らす中で、この国の文化的な背景や制度、社会の動向を、外からではなく「内側から」理解してきたと自負しています。学術、職業、文化の各分野にまたがるこうした経験の積み重ねは、イタリア文化の発信と、日伊間の文化的対話のさらなる深化に、責任感と奉仕の精神をもって貢献するための、確かな基盤になると考えています。"
            ),

            "read_more": "詳しい経歴. . .",
            "read_less": "閉じる",

            "count_years_in_japan_label": "日本での年数",
            "count_cultural_years_label": "文化活動の年数",
            "count_novels_value": "4",
            "count_novels_label": "小説",
            "count_papers_value": "2",
            "count_papers_label": "学術論文",


  


            "writing_title": "著作",
            "writing_subtitle": "書籍",
            "book1_url": "https://www.maurispagnol.it/en/book/tommaso-scotti-lombrello-dellimperatore-9788830456464",
            "book1_desc": "歌舞伎町で一人の男の遺体が発見される。凶器はあまりにもありふれた、一本のビニール傘。そこから想定外の指紋が検出されたとき、混血の警部・西田武は「ありえない事件」に直面する。捜査と現代日本社会を鋭く描き出すノワール。",
            "book2_url": "https://www.maurispagnol.it/en/book/tommaso-scotti-le-due-morti-del-signor-mihara-9788830459168",
            "book2_desc": "引退した実業家・見原氏が自宅で殺害されているのが見つかる。常識では説明できないこの事件を追う中で、西田警部は、ごく普通の人生の裏に潜む影と、日本社会に横たわる沈黙に向き合うことになる。",
            "book3_url": "https://www.maurispagnol.it/en/book/tommaso-scotti-i-diavoli-di-tokyo-ovest-9788830460836/ns",
            "book3_desc": "警視庁に緊張が走る。都内の小さな公園で発見された遺体のポケットから、西田警部の名刺が見つかったのだ。真相を追ううちに、西田は東京西部の街と、暴走族と呼ばれる若者たちの世界へと踏み込んでいく。そこに待っていたのは、個人的であり社会的でもある謎だった。",
            "book4_url": "https://www.maurispagnol.it/en/book/tommaso-scotti-il-segreto-del-vecchio-signor-nakamura-9788830462144",
            "book4_desc": "2018年の東京。元刑事の中村は、日本史上最も有名な未解決事件の一つ――1968年の三億円事件――から50年を迎え、再び過去と向き合うことになる。記憶と後悔、そして「被害者なき犯罪」が残した余韻を描く、静かで人間的な物語。",

            "cultural_title": "文化活動",
            "cultural_subtitle": "執筆・文化発信・文化的な取り組み",
            "cultural_box1_title": "文学活動",
            "cultural_box1_text": (
                "現代日本を舞台にしたフィクション作品を、イタリアの主要出版社から刊行。"
                "執筆を通じて、現代日本社会の社会的・文化的・歴史的テーマを扱っています。"
            ),
            "cultural_box2_title": "文化発信",
            "cultural_box2_text": (
                "イタリアの読者に向けた継続的な文化発信。文章、公開イベント、SNS、編集活動を通じて、"
                "ステレオタイプや単純化を超えた日本像を伝えることを目的としています。"
            ),
            "cultural_box3_title": "芸術的実践",
            "cultural_box3_text": (
                "文化理解の手段として、芸術／鍛錬系の実践にも継続的に取り組んでいます。"
                "武道（特に日本での剣道）、書道（2017年より書道院〈Shodan-in〉所属）、"
                "そして30年以上学んでいるピアノ。"
            ),
            "cultural_box4_title": "異文化経験",
            "cultural_box4_text": (
                "日本での生活と仕事は10年以上。国際的な職場・文化環境で培った経験を背景に、"
                "制度・社会・文化のダイナミクスに日常的に関わってきました。"
            ),

            "contact_title": "お問い合わせ",
            "contact_subtitle": "連絡する",
            "contact_address_title": "所在地",
            "contact_social_title": "SNS",

            "form_name_placeholder": "お名前",
            "form_email_placeholder": "メールアドレス",
            "form_subject_placeholder": "件名",
            "form_message_placeholder": "メッセージをご記入ください",
            "form_submit": "送信",
            "form_sending": "送信中…",

            "form_msg_minlen4": "4文字以上で入力してください",
            "form_msg_valid_email": "有効なメールアドレスを入力してください",
            "form_msg_subject_minlen4": "件名は4文字以上で入力してください",
            "form_msg_write_something": "メッセージを入力してください",

            "conference_title": "学会・会議一覧",
            "close": "閉じる",

            "conf_1_title": "若手数学者と産業界の合同セミナー",
            "conf_1_place": "東京大学（東京・日本）",
            "conf_1_date": "2014年10月",
            "conf_2_title": "第5回 日台 若手応用数学ワークショップ",
            "conf_2_place": "国立清華大学（新竹・台湾）",
            "conf_2_date": "2014年2月",
            "conf_3_title": "日・ハンガリー 応用数学と非線形ダイナミクス会議",
            "conf_3_place": "ブダペスト工科経済大学（ブダペスト・ハンガリー）",
            "conf_3_date": "2013年12月",
            "conf_4_title": "数理モデリングと応用に関する国際会議",
            "conf_4_place": "明治大学（東京・日本）",
            "conf_4_date": "2013年11月",
            "conf_5_title": "生態系等を対象とする反応拡散方程式PDE会議（NIMS-KMRS）",
            "conf_5_place": "KAIST（大田・韓国）",
            "conf_5_date": "2013年10月",
            "conf_6_title": "個体群動態と生態学におけるモデル",
            "conf_6_place": "オスナブリュック（ドイツ）",
            "conf_6_date": "2013年8月",
            "conf_7_title": "ReaDiLab ワークショップ（N2-days）",
            "conf_7_place": "明治大学（東京・日本）",
            "conf_7_date": "2013年7月",
            "conf_8_title": "数理生物学セミナー（MIMS）",
            "conf_8_place": "明治大学（東京・日本）",
            "conf_8_date": "2013年6月",

            "contact_ok": "ありがとうございます。できるだけ早く返信します。",
            "contact_missing": "必須項目が未入力です。",
            "contact_server_config": "サーバー設定エラーです。",
            "contact_auth_err": "メール認証エラーです。SNSからご連絡ください。",
            "contact_generic_err": "エラーが発生しました :/ しばらくしてから再度お試しいただくか、SNSからご連絡ください。",
        },
    }

    return T[lang]


def render_index(lang: str):

    age = calc_age(BIRTHDATE)
    today = date.today()
    count_years_in_japan_value = full_years_since(IN_JAPAN_SINCE, today=today)
    count_cultural_years_value = full_years_since(WRITING_SINCE, today=today)

    return render_template(
        "index.html",
        year=datetime.now().year,
        count_years_in_japan_value=count_years_in_japan_value,
        count_cultural_years_value=count_cultural_years_value,
        age=age,
        lang=lang,
        t=get_translations(lang),
    )


@app.route("/")
@app.route("/index", methods=["GET", "POST"])
def index():
    return render_index(lang_from_host("it"))


@app.route("/en", methods=["GET"])
def index_en():
    return render_index("en")


@app.route("/jp", methods=["GET"])
def index_jp():
    return render_index("jp")

@app.route("/it", methods=["GET"])
def index_it():
    return render_index("it")





@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    mail = request.form.get("email", "").strip()
    subj = request.form.get("subject", "").strip()
    message_text = request.form.get("message", "").strip()

    # language hint (preferred), fallback to url_from
    lang = (request.form.get("lang", "") or "").lower().strip()

    url_from = request.form.get("url_from", "")
    if lang not in ("it", "en", "jp"):
        if url_from.endswith("/en") or url_from.endswith("/en/"):
            lang = "en"
        elif url_from.endswith("/jp") or url_from.endswith("/jp/"):
            lang = "jp"
        else:
            lang = "it"

    t = get_translations(lang)

    # --- Anti-spam: honeypot ---
    if request.form.get("company", "").strip():
        return jsonify("Thank you!"), 200

    # --- Anti-spam: time trap ---
    ts = request.form.get("ts", "")
    try:
        ts = int(ts) / 1000.0
    except Exception:
        ts = None

    if not ts or (time.time() - ts) < 3:
        return jsonify("Thank you!"), 200

    # Basic validation
    if not mail or not message_text:
        return jsonify(t["contact_missing"]), 400

    body_text = f"From: {mail}\nName: {name}\n\n{message_text}"

    msg = MIMEMultipart()
    msg["Subject"] = f"From {name}: {subj}" if name else f"Contact form: {subj}"
    msg["From"] = os.environ.get("EMAIL")  # sender authenticated
    msg["To"] = os.environ.get("EMAIL_TO", "")

    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    smtp_user = os.environ.get("EMAIL")
    smtp_pwd = os.environ.get("PASSWORD")
    target_email = os.environ.get("EMAIL_TO")

    # Fail fast if env vars missing (common on Heroku)
    if not smtp_user or not smtp_pwd or not target_email:
        app.logger.error("Missing EMAIL/PASSWORD/EMAIL_TO env vars")
        return jsonify(t["contact_server_config"]), 500

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pwd)
            server.sendmail(smtp_user, [target_email], msg.as_string())

        return jsonify(t["contact_ok"])

    except SMTPAuthenticationError:
        app.logger.exception("SMTP auth failed (Gmail). Likely need an App Password.")
        return jsonify(t["contact_auth_err"]), 500

    except SMTPException:
        app.logger.exception("SMTP error while sending email")
        return jsonify(t["contact_generic_err"]), 500

    except Exception:
        app.logger.exception("Unexpected error in /contact")
        return jsonify(t["contact_generic_err"]), 500
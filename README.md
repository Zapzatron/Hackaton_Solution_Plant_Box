# Hackaton ООО «СОЛЮШН» (Компания «Плант-Бокс»)

Данный репозитории является решением задания от ООО "Солюшн" командой Don`t even try.

### Участники:

Александр Клочай&ensp;&ensp;&ensp;&emsp;Павел Вязников&ensp;&ensp;Сергей Русинов&ensp;&ensp;Николай Королев&ensp;&ensp;Глеб Сапега  
&nbsp;Software Engineer &ensp;&emsp;&emsp;&emsp;Teamlead	&emsp;&emsp;&ensp;Software Engineer	 &emsp;Labeling team	&emsp;&emsp;Labeling team  
t.me/KlochayAlexander  &ensp;&emsp;t.me/pavviaz	&emsp;&emsp;t.me/Ogyre4ik3	&emsp;t.me/ll_Cecilion_ll	 &emsp;&ensp;t.me/Lo0pik

Мы представляем систему для помощи фермерам (и не только) для определения наиболее подходящих почве культур.  
Бот помогает спрогнозировать, какие растения подойдут под заданный тип земли по её описанию и подскажет  
особенности культуры, периоды посева и сбора.  
Каждый человек сможет посадить наиболее подходящие растения для своего огорода и получить наилучший урожай  
Особенность нашего решения в том, что мы используем комбинацию больших языковых моделей (LLM),  
а также уникальных сборников дикорастущих лекарственных растений,  
что позволяет получить информацию о произрастании любых культур наиболее точно и информативно.  
Стек решения: Python, Transformers, Torch, pyTelegramBotAPI  


### Описание работы бота:
Команда /menu вызывает меню  
Бот может предоставить топ 3 растений по указанным параметрам.  
Что нужно сделать для этого?
1. Вызови /info_plant
2. Ввести параметры, по которым будет производиться поиск (тип почвы, город)
3. Подождать некоторое время

Пример:  
Ввод пользователя: /info_plant  
Ввод пользователя: чернозем, Кавказ  
Информация от бота:  
Топ 3 растений по заданным критериям:  
1.АДЕНОСТИЛЕС РОМБОЛИСТНЫЙ  
Ареалы произрастания аденостилеса ромболистного: Кавказ, Малая Азия, Северный Кавказ (все республики и края),  
Азербайджан, Армения, Грузия.  
2.СКУМПИЯ КОЖЕВЕННАЯ  
Средиземноморье, Южная Европа, Северная Африка, Азия (Турция, Иран, Пакистан, Индия, западные и южные провинции Китая),  
Россия (южные районы европейской части, Северный Кавказ), Азовское море, Каспийское море, Черное море.  
3.АЛТЕЙ ЛЕКАРСТВЕННЫЙ  
Ареалы произрастания алтея лекарственного: европейская часть России, юг Западной Сибири, некоторые районы Кавказа,  
северная граница лесостепной зоны, южная граница ареала в европейской части совпадает с государственной границей России,  
северная граница сибирской части ареала проходит между 55° и 56° параллелями с.ш., западная граница распространения алтея  
огибает с запада Омск и спускается на юго-восток до границы с Казахстаном, южная граница ареала проходит  
по государственной границе России. 

Сам бот: https://t.me/Plant_Info_Bot или @Plant_Info_Bot

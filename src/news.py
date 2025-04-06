class NewsLinks:
    def __init__(self):
        self.news_sources = {
            "suspilne": {
                "name": "Суспільне Тернопіль",
                "url": "https://suspilne.media/ternopil/"
            },
            "chortkiv": {
                "name": "Чортків.City",
                "url": "https://chortkiv.city/"
            }
        }

    def get_news_sources(self):
        """Отримати список доступних новинних ресурсів"""
        formatted_sources = "*📰 Доступні новинні ресурси:*\n\n"
        for source_id, source_info in self.news_sources.items():
            formatted_sources += f"*{source_info['name']}*\n[Перейти на сайт]({source_info['url']})\n\n"
        return formatted_sources

    def get_source_link(self, source_id):
        """Отримати посилання на конкретне джерело новин"""
        if source_id in self.news_sources:
            source = self.news_sources[source_id]
            return f"*📰 {source['name']}*\n[Перейти на сайт]({source['url']})"
        return "❌ Вказане джерело новин не підтримується" 
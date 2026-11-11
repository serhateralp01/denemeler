# Vault Builder — Roadmap

Kaldığımız yer ve sıradaki işler. Yeni bir session'da önce bu dosyayı oku.

## Durum (v5)

- [x] Login'siz Twitter metni (syndication API), paralel fetch
- [x] Web sayfaları için trafilatura (sayfanın gövde metni)
- [x] OpenRouter batch sınıflandırma (`openai/gpt-oss-120b:free`)
- [x] Graph yapısı: `01 - Notes` / `02 - People` / `03 - Topics` (7 adet) / `04 - Concepts` (not başına en fazla 2) + `Home.md`
- [x] `inbox/` klasörü: içine atılan her dosyadaki URL'ler okunur
- [ ] **OpenRouter 401 "Missing Authentication header"**: key girili olduğu hâlde oluyor. Auth header artık `add_unredirected_header` ile gönderiliyor. Doğrulanmadı, çıktıdaki `[ai] key: ...` satırına bak.

## Senden beklenen veriler (unutma)

Hepsini `inbox/` klasörüne at. Format önemli değil, script dosyanın içindeki URL'leri buluyor.

- [ ] **Twitter/X bookmarks**: export ya da URL listesi
- [ ] **Yeni Apple Notes**: notu kopyalayıp `.txt` olarak kaydet
- [ ] **Diğer kaynaklar** (Safari okuma listesi, iPhone tab'leri vb.)

> Not: `inbox/` gitignore'da değil. Kişisel link listesinin GitHub'a gitmesini istemiyorsan söyle, gitignore'a ekleyelim.

## Sıradaki büyük iş: arama + filtre + ağı görsel inceleme

Hedef: vault'ta konu, kişi, concept ve kaynağa göre arayıp filtreleyebilmek, ağı görsel olarak gezebilmek.

İki seçenek var:

1. **Obsidian içinde kalmak**: native Graph view (filtreler + gruplara renk) ve Dataview sorguları. Ek araç gerekmiyor ama filtreleme sınırlı.
2. **Ayrı bir explorer (önerilen)**: script vault'u tararken `graph.json` da üretir. Tek dosyalık bir HTML sayfası bu dosyayı okur:
   - full-text arama (başlık, özet, tweet metni)
   - topic / kişi / concept / kaynak / tarih filtreleri
   - force-directed graph: bir node'a tıklayınca komşuları vurgulanır, notu Obsidian'da açan `obsidian://` linki
   - Obsidian'a dokunmaz, yalnızca okur

Karar verilecekler: (1) mi (2) mi, ya da ikisi birden; explorer lokal mi açılacak, yoksa paylaşılabilir bir sayfa mı olacak.

## Açık konular

- Instagram içeriği hâlâ çekilmiyor (login gerekiyor)
- Google Docs/Drive linkleri: içerik yok, sadece URL'den sınıflandırılıyor
- Concept'lerin birleştirilmesi: AI benzer concept'ler üretirse (`ai-agents` / `agents`) bir alias/merge adımı gerekebilir

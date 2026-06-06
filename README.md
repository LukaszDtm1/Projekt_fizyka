# # Symulacja Rozchodzenia się Fal: Ośrodek Dyskretny

Projekt zaliczeniowy z fizyki demonstrujący propagację fali mechanicznej w jednowymiarowym ośrodku dyskretnym. Ciągły ośrodek sprężysty został tu zamodelowany jako skończony łańcuch mas połączonych liniowymi sprężynami. 

Aplikacja posiada graficzny interfejs (GUI), który pozwala na zmianę parametrów fizycznych w czasie rzeczywistym i obserwację ich wpływu na zachowanie fal.

## Funkcjonalności
* **Silnik fizyczny:** Równania ruchu rozwiązywane numerycznie metodą Eulera w oparciu o II zasadę dynamiki Newtona i prawo Hooke'a.
* **Interaktywny interfejs:** Sterowanie parametrami układu:
  * Liczba mas (N)
  * Masa pojedynczego punktu (m)
  * Współczynnik sprężystości (k)
* **Generowanie fal:** Możliwość wzbudzenia impulsu falowego za pomocą przycisku lub interakcja myszką bezpośrednio na wykresie.
* **Zoptymalizowany rendering:** Wykorzystanie techniki *blittingu* w Matplotlib dla płynnej animacji w okienku PyQt6.

Aby program działał, należy zainstalować i zaimportować następujące biblioteki:

```bash
pip install numpy matplotlib PyQt6


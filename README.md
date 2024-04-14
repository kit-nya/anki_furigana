# Anki Automatic Kanji Readings and Definitions Add-on

Welcome to my Anki add-on! This add-on provides the ability to automatically populate fields in Anki flashcards with kanji readings and definitions. The add-on utilizes JMdict (Japanese-Multilingual Dictionary) for the definition lookups. It was created primarily because I was a little annoyed that the rubytext never seemed to line up with characters properly with any of the existing addons I could find.

Plus, I didn't really get why I needed to use the internet when there's already readily available dictionaries to be downloaded.

## Features
With this add-on, you can:
- Automatically populate Anki flashcards with kanji readings and definitions.
- Limit the number of definitions to top X number
- Work entirely offline.

## References

I have used JMdict for fetching kanji readings and definitions.
More information about JMdict can be found here: [JMdict](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project)

## Screenshots
Here's an example of what this addon does for a note, please note that there are no note types provided with the addon so you'll need to make your own.

From this
![Input](https://raw.githubusercontent.com/kit-nya/anki_furigana/master/docs/enter_text.png)
To this
![Output](https://raw.githubusercontent.com/kit-nya/anki_furigana/master/docs/tab_result.png)

## Usage

After installation, please update the following settings found here:
![Settings](https://raw.githubusercontent.com/kit-nya/anki_furigana/master/docs/settings_location.png)

The following settings are provided
![SettingsOptions](https://raw.githubusercontent.com/kit-nya/anki_furigana/master/docs/settings_example.png)

- Input field: This is the field in which Kanji is entered
- Furigana field: This is where rubytext will be generated for the Kanji input
- Kana field: This is the hiragana reading from the input field
- Definition field: This gives you the top X definitions as defined in "Number of Defs"
- Type field: Gives you the type of word, keiyoushi, meishi etc
- Number of Defs: Limits the number of definitions in the Definition field

## Contribution 

Your contributions are welcome! If you have any ideas or suggestions, please feel free to [Submit an issue](https://github.com/kit-nya/anki_furigana/issues/new).

## License

Please see the [LICENSE](https://raw.githubusercontent.com/kit-nya/anki_furigana/master/LICENSE) file for details.
# Market brief: how to update it

The brief lives at `/market-brief/`. The page draws every figure from one file,
`market-brief/data.json`. Nothing on the page is typed by hand. To refresh the
brief you replace that file and commit.

(This `_tools` folder is not published. GitHub Pages skips folders that start
with an underscore.)

## Monthly update, about 10 minutes

1. **Export the data** from [USA Trade Online](https://usatrade.census.gov/)
   (free account), report *Imports > Harmonized System (HS) > District-level*.
   Use the same layout as the file in `source/`:

   | Setting | Select |
   |---|---|
   | Commodity | `0910990500`, `0910990600`, `0909610000`, `0910995000`, `0909210000` |
   | Country | Egypt, India, Turkey, World Total |
   | District | All Districts |
   | Time | last full year (e.g. `2025`), year to date (e.g. `2026 through October`), latest month (e.g. `October 2026`) |
   | Measures | Customs Value (Gen), CIF Value (Gen), Calculated Duty, Quantity 1 (Gen). Customs Unit Value (Gen) is optional and is used as a cross-check. |
   | Layout | Measures down the side; commodity, country and time across the top |

   Download as CSV and save it in `_tools/market-brief/source/` with the date
   in the name, e.g. `usa-trade-online-2026-12-16.csv`.

2. **Build the data file** from the repo root:

   ```
   python3 _tools/market-brief/build_data.py _tools/market-brief/source/usa-trade-online-2026-12-16.csv
   ```

   The script checks the export (all cells present, CIF not below customs
   value, named origins not above the world total, unit values equal to
   Census's own) and stops with a message if anything is off. It then prints
   the headline figures the page will show. Read them before committing.

3. **Look at the page** locally, then commit `market-brief/data.json` and the
   new CSV:

   ```
   python3 -m http.server 8000      # then open http://localhost:8000/market-brief/
   ```

## What the page computes

For each product, origin and period, `data.json` holds four raw numbers:
weight (kg), customs value, CIF value and calculated duty, all in US dollars.
The page derives the rest:

| Shown as | Formula |
|---|---|
| Product (per lb or kg) | customs value / weight |
| Freight & insurance | (CIF value - customs value) / weight |
| Duty | calculated duty / weight |
| Landed cost | (CIF value + calculated duty) / weight |
| Duty paid (%) | calculated duty / customs value |
| Share of US imports | origin weight / all-origin weight |
| Other origins | all origins minus the origins shown by name |
| Change vs prior year | year-to-date average / full prior-year average - 1 |

Pounds per kilogram: 2.20462262185. Origins under 2% of year-to-date weight are
folded into "Other origins" on the charts (`meta.minShare`); the full table
lists every origin.

## Changing what the brief covers

Edit the three blocks at the top of `build_data.py`, then rebuild:

- `LINES`: tariff code to product. Add a code to an existing product to
  combine it, or to a new product id.
- `PRODUCTS`: display order, name and the one-line "Reading this" note.
  `originNotes` puts a short caution under an origin's name.
- `ORIGINS` and `ORIGIN_NAMES`: countries in the export. For a new country,
  also add a flag symbol (`<symbol id="f-XX">`) and a colour (`OCOL`, `OTXT`)
  in `market-brief/index.html`. Without them the page falls back to a globe
  icon and a neutral colour.

## Links

- Open on a product: `https://stoneferrytrading.com/market-brief/#dill`
  (`#thyme`, `#seeds`, `#dill`, `#coriander`).
- Tag a link to know it was opened: add `?r=` and a short code before the `#`,
  e.g. `https://stoneferrytrading.com/market-brief/?r=b053#dill`. Use a short
  opaque code. Never put a name or an email address in a link.

## Analytics

`assets/site-analytics.js` is loaded by every page. Paste a Microsoft Clarity
project ID into it to switch analytics on (instructions are in the file).
The brief reports these events:

| Event | When |
|---|---|
| `brief_product_<id>` | a product tile is selected |
| `nav_market_brief`, `foot_market_brief` | the brief is opened from the home page |
| `brief_unit_lb`, `brief_unit_kg` | the unit is switched |
| `brief_calc_used`, `brief_calc_origin` | the calculator is used |
| `brief_cta_quote` | "Get a delivered quote" is clicked |
| `brief_cta_form`, `brief_cta_phone`, `brief_cta_email`, `brief_copy_email` | contact actions |
| `brief_open_numbers`, `brief_open_method` | a section is expanded |

The calculator is marked `data-clarity-mask`, so what visitors type is not
recorded, as the page promises.

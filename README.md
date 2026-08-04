# GCSC Land Use Change Emission Factor Extractor

A single-file static webapp that extracts **statistical land use change (sLUC)** and **jurisdictional direct land use change (jdLUC)** emission factors from the **WRI GCSC** (Global Cropland Scope-3 Carbon) database — by commodity, country, and sub-region (down to municipality level) — with co-product/by-product allocation where available. Includes result export to CSV.

## Source data

Pulled from [github.com/wri/GCSC](https://github.com/wri/GCSC) (Fitts et al., 2025):

- **sLUC emission factors** — 42 agricultural crops, global / ADM0 / ADM1 / ADM2 (municipality), reporting years 2020–2024, per gas (CO2e, CO2, CH4, N2O).
- **jdLUC emission factors** — oil palm, soy, cocoa at ADM0/ADM1/ADM2.
- **Co-product allocation tables** — oil palm, soy, cocoa co-products with allocation ratios & functional units.
- **GADM admin keys** — country (ADM0), state/province (ADM1), municipality (ADM2) names.
- **Yield factors** — ADM0 & ADM1.

## How to use

1. Select a **commodity**.
2. Choose **traceability level** — Municipality (Admin 2) → Sub-national (Admin 1) → National (Admin 0), finest-first.
3. Select **country**, then **state / province**, and for municipality level a **municipality / county**.
4. Pick **reporting year** and **gas**.
5. If the commodity has co-products (oil palm, soy, cocoa), select the **co-product** — the raw crop EF is multiplied by its allocation ratio.
6. Optionally enter **volume sourced** to compute total emissions, then click **Extract Emission Factor**.
7. Click **⬇ Export result as CSV** to download the extracted result.

### sLUC vs jdLUC

For **oil palm, soy, and cocoa**, the tool automatically prefers the **jdLUC** emission factor where jdLUC data exists for the selected jurisdiction (oil palm in ~36 countries; soy in Argentina, Bolivia, Brazil, Paraguay, Uruguay; cocoa in Côte d'Ivoire & Ghana). Otherwise it uses the statistical **sLUC** factor. Check the "Method" tag on the result to confirm which was used. Co-product tables provide CO2e only; other gases are derived from the raw crop EF × allocation ratio.

## Structure

```
deploy/
├── index.html      # single-file app (CSS + JS inlined)
└── data/           # JS data bundles (index.js + sLUC/jdLUC/co/gadm/yield)
```

## Deploy

Drag the `deploy/` folder to [Netlify Drop](https://app.netlify.com/drop) or serve with any static host. No build step, zero external dependencies. Note: opening `index.html` directly via double-click (file://) works — all data is loaded via static `<script>` tags.

## Disclaimer

This is a simplified analysis and does not capture all nuances of the standards or methodologies. Emission factors are reproduced as-is from the source database. This tool does not constitute emissions accounting advice. Always refer to the actual source documents and the GHG Protocol Land Sector and Removals Standard for authoritative guidance.

Citation: Fitts, L.A., et al. 2025. "Statistical land use change emissions from deforestation and land occupation for crops." Technical Note. Washington, DC: World Resources Institute. Available at doi.org/10.46830/writn.25.00085.

import { createRequire } from 'node:module';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const baseURL = process.env.BOXPLOTR_URL || 'http://127.0.0.1:3838';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const failures = [];
page.on('pageerror', error => failures.push(`pageerror: ${error.message}`));
page.on('console', message => {
  if (message.type() === 'error' && !message.text().includes('fonts.googleapis.com')) {
    failures.push(`console: ${message.text()}`);
  }
});

async function plotSignature() {
  await page.waitForFunction(() => {
    const image = document.querySelector('#boxPlot img');
    return image && image.complete && image.naturalWidth > 0;
  });
  return page.locator('#boxPlot img').getAttribute('src');
}

async function waitForNewPlot(previous) {
  await page.waitForFunction(oldSrc => {
    const image = document.querySelector('#boxPlot img');
    return image && image.complete && image.naturalWidth > 0 && image.getAttribute('src') !== oldSrc;
  }, previous);
}

try {
  await page.goto(baseURL, { waitUntil: 'networkidle' });
  if (!(await page.locator('h1').innerText()).includes('BoxPlotR')) throw new Error('BoxPlotR heading missing');

  await page.locator('a[data-value="Data visualization"]').click();
  const classicPlot = await plotSignature();

  const downloadPromise = page.waitForEvent('download');
  await page.locator('#downloadPlotPDF').click();
  const download = await downloadPromise;
  const downloadPath = path.join(os.tmpdir(), `boxplotr-${Date.now()}.pdf`);
  const downloadFailure = await download.failure();
  if (downloadFailure) throw new Error(`PDF download failed: ${downloadFailure}`);
  await download.saveAs(downloadPath);
  if (fs.statSync(downloadPath).size < 1000) throw new Error('Downloaded PDF is unexpectedly small');
  fs.unlinkSync(downloadPath);

  await page.locator('input[name="plotEngine"][value="ggplot"]').check();
  await waitForNewPlot(classicPlot);
  const modernPlot = await plotSignature();
  if (modernPlot === classicPlot) throw new Error('Plot did not update after engine switch');

  await page.locator('a[data-value="Data upload"]').click();
  await page.locator('input[name="sampleData"][value="3"]').check();
  await page.locator('a[data-value="Data visualization"]').click();
  const beforeLog = await plotSignature();
  await page.locator('#myNotch').check();
  await page.locator('#logScale').check();
  await waitForNewPlot(beforeLog);
  await plotSignature();
  const validationError = page.locator('#boxPlot.shiny-output-error');
  if (await validationError.count()) throw new Error(`Log/notch rendering failed: ${await validationError.innerText()}`);

  await page.locator('a[data-value="Data upload"]').click();
  await page.locator('input[name="dataInput"][value="3"]').check();
  await page.locator('#myData').fill('Label,SampleA\na,1\nb,2');
  await page.locator('#myData').dispatchEvent('change');
  await page.locator('a[data-value="Data visualization"]').click();
  await page.locator('#boxPlot.shiny-output-error-validation').waitFor();
  const message = await page.locator('#boxPlot.shiny-output-error-validation').innerText();
  if (!message.includes('All data columns must be numeric')) throw new Error(`Unexpected validation message: ${message}`);

  if (failures.length) throw new Error(failures.join('\n'));
  console.log('Playwright browser checks passed');
} finally {
  await browser.close();
}

import React from "react";
import { Calculator, Percent, DollarSign, ArrowRight, ShieldCheck, Scale } from "lucide-react";

export default function TariffCalculator() {
  const [cifValue, setCifValue] = React.useState<number>(12500);
  const [useETLS, setUseETLS] = React.useState<boolean>(true);
  const [standardDutyRate, setStandardDutyRate] = React.useState<number>(10); // 10% for agricultural raw rice paddy/husk intermediate
  const [vatRate, setVatRate] = React.useState<number>(0); // 0% because rice is frequently VAT exempted under Malian Decrees
  const [statisticalFeeExempt, setStatisticalFeeExempt] = React.useState<boolean>(false);

  // Math conversions
  const dutyRateUsed = useETLS ? 0 : standardDutyRate;
  const customsDuty = Number(((cifValue * dutyRateUsed) / 100).toFixed(2));
  
  const statisticalFeeVal = statisticalFeeExempt ? 0 : Number((cifValue * 0.01).toFixed(2)); // 1%
  const ecowasLevyVal = Number((cifValue * 0.005).toFixed(2)); // 0.5%
  const uemoaLevyVal = Number((cifValue * 0.008).toFixed(2)); // 0.8% Sol levy
  
  const subTotalBeforeVat = cifValue + customsDuty + statisticalFeeVal + ecowasLevyVal + uemoaLevyVal;
  const vatValue = Number(((subTotalBeforeVat * vatRate) / 100).toFixed(2));
  const totalTaxesPayable = customsDuty + statisticalFeeVal + ecowasLevyVal + uemoaLevyVal + vatValue;
  const grandTotalLandCost = cifValue + totalTaxesPayable;

  return (
    <div id="tariff-calculator" className="border border-zinc-200 bg-white rounded-xl shadow-xs overflow-hidden">
      {/* Header */}
      <div className="bg-zinc-50 border-b border-zinc-200 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <Calculator className="h-5 w-5 text-amber-700" />
          <h2 className="font-sans font-semibold tracking-tight text-zinc-900 text-sm">
            Interactive Duty & Tariff Calculator (Mali Terminal)
          </h2>
        </div>
        <div className="text-zinc-500 text-xs font-mono">
          ETLS Simulator v2.0
        </div>
      </div>

      <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Parameters Column */}
        <div className="space-y-4">
          <h3 className="font-sans font-semibold text-zinc-800 text-xs pb-1 border-b border-zinc-100 flex items-center text-amber-900">
            <Scale className="h-3.5 w-3.5 mr-1" /> Input Parameters
          </h3>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-[11px] font-medium text-zinc-500 uppercase">Customs Value (CIF USD)</label>
              <span className="font-mono text-xs font-bold text-zinc-700">${cifValue.toLocaleString()}</span>
            </div>
            <input
              type="range"
              min="1000"
              max="100000"
              step="500"
              value={cifValue}
              onChange={(e) => setCifValue(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-200 rounded-lg appearance-none cursor-pointer accent-amber-700"
            />
          </div>

          <div>
            <label className="text-[11px] font-medium text-zinc-500 uppercase block mb-1.5">Trade Regime Mode</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setUseETLS(true)}
                className={`py-2 px-3 text-xs rounded border transition-all font-medium text-center flex flex-col items-center justify-center cursor-pointer ${
                  useETLS
                    ? "bg-amber-50 border-amber-600 text-amber-950"
                    : "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50"
                }`}
              >
                <span className="flex items-center">
                  <ShieldCheck className={`h-3.5 w-3.5 mr-1 ${useETLS ? 'text-amber-700' : 'text-zinc-400'}`} />
                  ETLS Origin
                </span>
                <span className="text-[9px] mt-0.5 opacity-80 text-center font-normal">Exempts Duty (0%)</span>
              </button>
              <button
                type="button"
                onClick={() => setUseETLS(false)}
                className={`py-2 px-3 text-xs rounded border transition-all font-medium text-center flex flex-col items-center justify-center cursor-pointer ${
                  !useETLS
                    ? "bg-zinc-900 border-zinc-950 text-white"
                    : "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50"
                }`}
              >
                <span>Non-ETLS Border</span>
                <span className="text-[9px] mt-0.5 opacity-80 text-center font-normal">Standard ECOWAS CET</span>
              </button>
            </div>
          </div>

          {!useETLS && (
            <div>
              <label className="text-[11px] font-medium text-zinc-500 uppercase block mb-1">CET Duty band</label>
              <div className="grid grid-cols-4 gap-1.5">
                {[5, 10, 20, 35].map((rate) => (
                  <button
                    key={rate}
                    type="button"
                    onClick={() => setStandardDutyRate(rate)}
                    className={`p-1.5 border rounded text-xs text-center font-mono cursor-pointer ${
                      standardDutyRate === rate
                        ? "bg-zinc-800 text-white border-zinc-900"
                        : "bg-white text-zinc-600 border-zinc-200 hover:bg-zinc-50"
                    }`}
                  >
                    {rate}%
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-zinc-500 mt-1">
                (Rice standard CET is generally 10% (Category 2) or 20% (Category 3))
              </p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 pb-2">
            <div>
              <label className="text-[11px] font-medium text-zinc-500 uppercase block mb-1">VAT Rate</label>
              <select
                value={vatRate}
                onChange={(e) => setVatRate(Number(e.target.value))}
                className="w-full text-xs border border-zinc-200 rounded px-2.5 py-1.5 focus:outline-none focus:border-amber-600 bg-white"
              >
                <option value={0}>0% (Raw Cereal Exempt)</option>
                <option value={18}>18% (Mali Std VAT)</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-medium text-zinc-500 uppercase block mb-1">Statistical Fee</label>
              <select
                value={statisticalFeeExempt ? "yes" : "no"}
                onChange={(e) => setStatisticalFeeExempt(e.target.value === "yes")}
                className="w-full text-xs border border-zinc-200 rounded px-2.5 py-1.5 focus:outline-none focus:border-amber-600 bg-white"
              >
                <option value="no">1% Standard Fee</option>
                <option value="yes">Exempt Statistical</option>
              </select>
            </div>
          </div>
        </div>

        {/* Calculation Summary Column */}
        <div className="bg-zinc-50/70 border border-zinc-100 p-4 rounded-lg flex flex-col justify-between">
          <div>
            <h3 className="font-sans font-semibold text-zinc-800 text-xs pb-1 border-b border-zinc-200/60 mb-3 flex items-center justify-between">
              <span>Levy & Duty Breakdown</span>
              <span className={`text-[10px] px-2 py-0.5 rounded font-bold font-mono ${useETLS ? 'bg-amber-100 text-amber-900' : 'bg-zinc-200 text-zinc-800'}`}>
                {useETLS ? "ETLS APPLIED" : "STANDARD CET"}
              </span>
            </h3>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between">
                <span className="text-zinc-500">Declared Value (CIF):</span>
                <span className="font-mono text-zinc-800 font-medium">${cifValue.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-500 flex items-center">
                  Import Customs Duty ({dutyRateUsed}%):
                </span>
                <span className="font-mono text-zinc-800 font-medium">
                  {useETLS ? (
                    <span className="text-emerald-700 font-semibold bg-emerald-55/70 px-1.5 py-0.5 rounded text-[10px]">Exempt (0%)</span>
                  ) : (
                    `$${customsDuty.toLocaleString()}`
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Mali Statistical Fee (1%):</span>
                <span className="font-mono text-zinc-800">
                  {statisticalFeeExempt ? "$0.00" : `$${statisticalFeeVal.toLocaleString()}`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">ECOWAS Community Levy (0.5%):</span>
                <span className="font-mono text-zinc-800">${ecowasLevyVal.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">WAEMU PC Solidarity Levy (0.8%):</span>
                <span className="font-mono text-zinc-800">${uemoaLevyVal.toLocaleString()}</span>
              </div>
              <div className="flex justify-between border-t border-zinc-200/50 pt-2">
                <span className="text-zinc-500">VAT Amount ({vatRate}%):</span>
                <span className="font-mono text-zinc-800">${vatValue.toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-zinc-200">
            <div className="flex justify-between items-baseline mb-1">
              <span className="text-[11px] font-semibold text-zinc-600 uppercase">Taxes & Levies Payable</span>
              <span className="font-mono text-base font-bold text-amber-900">${totalTaxesPayable.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-[10px] font-mono text-zinc-500">Grand Landed Cost:</span>
              <span className="font-mono text-xs text-zinc-600">${grandTotalLandCost.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
